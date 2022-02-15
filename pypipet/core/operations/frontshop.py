from pypipet.core.sql.query_interface import *
from pypipet.core.model.product import Destination, Product, Variation
from .utility import get_front_shop_id
from copy import deepcopy

import logging
logger = logging.getLogger('__default__')

_DEBUG_ = False


def add_taxonomy_to_db(table_obj, session, shop_connector):
    categories = shop_connector.get_category_taxonomy()
    if categories:
        for cat in categories:
            db_insert_raw(table_obj, session, cat)
    else:
        logger.info('fetching taxonomy failed')


def load_products_from_shop(table_objs, session, shop_connector, 
                         start_from=1,  **kwargs):
    start_page = start_from
    while True:
        logger.debug(f'page {start_page}')
        res = shop_connector.get_products_at_shop(
                                  batch_size=shop_connector.batch_size, 
                                  page=start_page,
                                  **kwargs
                                  )
        if _DEBUG_ : logger.debug(f"total {len(res)}")
        if res is None or len(res) == 0:
            logger.debug('done sync')
            break
        
        add_product_to_db_bulk(table_objs, session, 
                                       shop_connector,res)
        start_page += 1
        if _DEBUG_ : break


def get_product_from_shop(shop_connector, 
                                destination_product_id, **kwargs):
    res = shop_connector.get_product_at_shop(destination_product_id,
                                             **kwargs)
    if res:
        return res

def add_product_to_db_bulk(table_objs, session, 
                            shop_connector,products:list, currency='USD'):
    for p in products:
        # if _DEBUG_: logger.debug(p)
        if p is None: continue
        add_product_with_variations_to_db(table_objs, session, 
                            shop_connector, p, currency=currency)

def add_product_with_variations_to_db(table_objs, session, 
                            shop_connector,p:dict, currency='USD'):
    add_product_to_db(table_objs, session, p['product'])
    if p.get('destinations') is None \
                or len(p['destinations']) == 0: 
        return
    for dest in p['destinations']:
        #print(p['destinations'])
        add_destination_to_db(table_objs, 
                            session, 
                            shop_connector.front_shop_id, 
                            dest,
                            currency=currency)


def add_product_to_db(table_objs, session, product_info: dict):
    if product_info is None: return 
    product = Product()
    #check category
    if product_info.get('category') is not None \
    and product_info.get('category').strip() != '' \
    and type(product_info.get('category')) is str:
        # print(product_info['product_name'])
        cat = _get_category_by_name(
                            table_objs.get('category'), 
                            session, 
                            product_info['category'])
        
        product_info.update(cat)
        del product_info['category']
    
    product.set_product(table_objs, product_info)
    
    return add_new_product(table_objs, session, product)


# def add_variation_to_db(table_objs, session, product_id: int,  variation_data: dict):
#     if variation_data.get('sku') is None:
#         logger.debug(f'missing {sku}')
#         return None

#     variation  = Variation() 
#     variation.set_variation(table_objs, variation_data)
    
#     #validate non-duplicate sku
#     exists = search_exist(table_objs.get(variation.__table_name__), 
#                           session, 
#                           {'sku': variation.sku})
#     if len(exists) > 0:
#         logger.debug(f'duplicate {variation.sku}')
#         return None

    
#     variation.set_attr('product_id', product_id)

#     res = add_to_db(table_objs.get(variation.__table_name__), 
#                      session, 
#                      variation)
#     if res is not None:
#         return variation


def add_destination_to_db(table_objs, session, front_shop_id, 
                                        dest_data, **kwargs):
    
    dest_data.update({
        'front_shop_id': front_shop_id,
        'is_current_price': True,
        'currency': kwargs.get('currency', 'USD')
    })
    if dest_data.get('available') is None:
        dest_data['available'] = True 
    
    ignore_exist = kwargs.get('ignore_exist', False)
    if not ignore_exist:
        exist = search_exist(table_objs.get('destination'), 
                                    session, {
                                        'sku': dest_data['sku'],
                                        'front_shop_id': front_shop_id
                                    })
        if exist and len(exist) > 0:
            #update 
            # update_data(table_objs.get('destination'),  session,
            #         dest_data, {'id': exist[0].id})
            logger.debug(f'destination exists {dest_data}')
            return 
   
    #add new 
    dest = Destination()
    dest.set_destination(table_objs, dest_data)
    
    add_to_db(table_objs.get(dest.__table_name__), session, dest)

def is_exist_destination(table_obj, session, dest_data):
    dest = search_exist(table_obj, session,{
        'front_shop_id': dest_data['front_shop_id'],
        'sku': dest_data['sku']
    })
    if dest is None or len(dest) == 0:
        return False 
    else:
        for d in dest:
            if d.is_current_price:
                logger.debug(f'data exist id {d.id}')
                dest_data['id'] = d.id
                return True 
        return False



def get_product_info(table_objs, session, shop_connector, identifier=None,
                    sku=None, product_id=None, include_published=False,
                    include_category=False, **kwargs):
    params = None
    if identifier is not None:
        params = {'identifier': identifier}
    elif product_id is not None:
        params = {'product_id': product_id}
    elif sku is not None:
        params = {'sku': sku}
    if params is None:
        logger.debug('invalid product params')
        return 
    
    variation_info = get_product_with_variations(
                     table_objs, 
                     session, 
                     params, 
                     include_published=include_published,
                     include_category=include_category, 
                     front_shop_id=shop_connector.front_shop_id)
    return variation_info

def add_product_to_shop(table_objs, session, shop_connector, product_info, 
                                    price=None, prices:dict=None, **kwargs):
    if product_info is None: return 
    
    if product_info.get('destinations'):
        logger.debug(f"has destinations, {product_info['destinations']}")
        return
    if (price is None and prices is None) or \
    (prices is not None and type(prices) is not dict):
        logger.debug('invalid product params')
        return 
    
    currency = kwargs.get('currency', 'USD')
    if product_info.get('variations') is None:
        #product without variations 
        product_info['price'] = price
        product_info['currency'] = currency
        res = shop_connector.add_product_to_shop(
                                             deepcopy(product_info),
                                             **kwargs) 

        if res is None:
            logger.debug(f"adding product to front shop failed {product_info['sku']}")
            return None
        #add to database
        res.update({
            'sku': product_info['sku'],
            'price': price,
            'destination_product_id': str(res['id'])
        })
        add_destination_to_db(table_objs, session, 
                             shop_connector.front_shop_id, 
                             res, currency=currency,
                             ignore_exist=kwargs.get('ignore_exist', True))
        return res
    else:
        for i, vari in enumerate(product_info['variations']):
            product_info['variations'][i]['currency'] = currency 
            if price: 
                product_info['variations'][i]['price'] = price 
            else:
                if prices.get(vari['sku']) is None:
                    logger.debug(f"missing price for sku {vari['sku']}")
                product_info['variations'][i]['price'] = \
                             prices.get(vari['sku'])
       
        assert kwargs.get('variation_attrs') is not None
        
        parent_id = kwargs.get('parent_id', product_info.get('parent_id'))
        
        res = shop_connector.add_product_to_shop(
                                             deepcopy(product_info),
                                             parent_id=parent_id,
                                             **kwargs) # return dict to res
        if res is None or len(res) == 0:
            logger.debug(f"adding product to front shop failed {product_info['identifier']}")
            return None
        for i, vari in enumerate(product_info['variations']):
            if res.get(vari['sku']):
                if price is None:
                    price =  prices.get(vari['sku'])

                dest_data= res[vari['sku']]
                dest_data.update({
                    'sku': vari['sku'],
                    'price': price,
                    'destination_product_id': str(dest_data['id'])
                })
                add_destination_to_db(table_objs, session, 
                             shop_connector.front_shop_id, 
                             dest_data, currency=currency,
                             ignore_exist=kwargs.get('ignore_exist', True))
                # dest_data.update({
                #     'sku': vari['sku'],
                #     'front_shop_id': shop_connector.front_shop_id,
                #     'price': price,
                #     'is_current_price': True,
                #     'available': True,
                #     'currency': currency,
                # })
                # exists = search_exist(table_objs.get('destination'), session, 
                #                      {'sku': vari['sku'],
                #                       'front_shop_id': shop_connector.front_shop_id,
                #                       'is_current_price': True,
                #                       'available': True})
                # if exists and len(exists) > 0:
                #     update_data(table_objs.get('destination'), session, 
                #                 dest_data,
                #                 {'id': exists[0].id})
                # else:
                #     add_json_to_db(table_objs.get('destination'), session, 
                #                    dest_data)
            else:
                logger.debug(f"missing results for sku {vari['sku']}")  
        return res  

def add_variation_to_shop(table_objs, session, shop_connector, 
                             sku:str, price:float, **kwargs):
    if shop_connector.front_shop_id is None:
        get_front_shop_id(table_objs, session, shop_connector)
    
    #transform data
    # variation_info = get_variation_info_by_sku(table_objs, session, sku, 
    #                  front_shop_id=shop_connector.front_shop_id)
    product_info = get_product_with_variations(table_objs, session, 
                    {'sku': sku}, 
                     include_published=False, 
                     front_shop_id=shop_connector.front_shop_id)
    
    if product_info is None:
        return 
    
    #check if it has been added but available_flag need update to True
    if product_info.get('set_available_flag'):
        #activate again 
        update_data(table_objs.get('destination'), 
                    session, 
                    {'available': True}, 
                    {'id': product_info['destination_id'] })
        logger.info(f"variation sku {sku} reactivated")
            
        return 

    if product_info.get('destinations') is not None:
        del product_info['destinations']
    
    # if the sku is one of the variations of a product
    if product_info.get('variations') and type(product_info['variations']) is list:
        if kwargs.get('ignore_variations'):
            product_info.update(product_info['variations'][0])
            del product_info['variations']
        else:
            logger.info('add as variation')
            return add_product_to_shop(table_objs, session, shop_connector, 
                       product_info, price=price, **kwargs)

    #add to frontshop 
    product_info['price'] = price
    product_info['currency'] = kwargs.get('currency', 'USD')
    res = shop_connector.add_product_to_shop(
                                             product_info,
                                             **kwargs)
    # if res is None:
    #     #if exist, update
    #     res = _update_product_at_frontshop_by_sku(table_objs, session, 
    #                                       shop_connector, 
    #                                       sku, product_info)
    # 
       
    if res is None:
        logger.debug(f'adding product to front shop failed {sku}')
        return None
    #add to database
    dest_data= res
    dest_data.update({
        'sku': sku,
        'price': price,
        'destination_product_id': str(dest_data['id'])
    })
    add_destination_to_db(table_objs, session, 
                    shop_connector.front_shop_id, 
                    dest_data, currency=product_info['currency'],
                    ignore_exist=kwargs.get('ignore_exist', True))
    
    return res


def get_cost_by_sku_from_db(table_obj, session, sku, params: dict=None):
    """apply when  skus have multiple suppliers"""
    if params is None: params = {}
    params['sku'] = sku
    exists = search_exist(table_obj, session, params)
    if len(exists) > 0:
        prices = [inv.cost for inv in exists]
        return sum(prices)/len(prices)

def update_product_to_db(table_objs, session, product_info: dict):
    params = {}
    if product_info.get('id') is not None:
        params['id'] = product_info['id']
    elif product_info.get('identifier') is not None:
        params['identifier'] = product_info['identifier']
    else:
        logger.debug('missing product id and identifier')
        return 
    #check category
    if product_info.get('category') is not None \
    and product_info.get('category').strip() != '' \
    and type(product_info.get('category')) is str:
        # print(product_info['product_name'])
        cat = _get_category_by_name(
                            table_objs.get('category'), 
                            session, 
                            product_info['category'])
        
        product_info.update(cat)
        del product_info['category'] 
    
    if product_info.get('short_description'):
        product_info['short_description'] = product_info['short_description'][:1000]
    update_data(table_objs.get('product'), session, product_info, 
                params)    

def update_variation_to_db(table_obj, session, variation_info: dict):
    update_data(table_obj, session, variation_info, 
                {'sku': variation_info['sku']})     

def update_destination_to_db(table_obj, session, dest_info: dict, front_shop_id):
    params ={
        'sku': dest_info['sku'],
        'front_shop_id': front_shop_id,
        'is_current_price': True
    }
    if dest_info.get('price') is not None:
        destination = update_destination_price(table_obj, 
                                    session, dest_info['price'], params)
    
    update_data(table_obj, session, dest_info, params)  

def update_front_shop_price_bulk(table_objs, session, shop_connector, data: list):
    if shop_connector.front_shop_id is None:
        get_front_shop_id(table_objs, session, shop_connector)
    for d in data:
        if d.get('price') is None: continue
        price = d['price']
        del d['price']

        d['front_shop_id'] = shop_connector.front_shop_id
        update_front_shop_price(table_objs, session, 
                            shop_connector, price, d)
    return data

def update_front_shop_price(table_objs, session, shop_connector, price:float, params:dict):
    if shop_connector.front_shop_id is None:
        get_front_shop_id(table_objs, session, shop_connector)
    #udpate database
    destination = update_destination_price(table_objs.get('destination'), 
                                              session, price, params)
    # print(destination.destination_product_id)
    if destination:
        #udpate front shop
        res = shop_connector.update_shop_product(
                            {'price': price}, 
                            product_id=destination.destination_product_id,
                            parent_id=destination.destination_parent_id
                            )
        
        return res

def update_product_at_front_shop_bulk(table_objs, session, shop_connector, 
                                   data_list: list, batch_size=50,  **kwargs):
    """bulk option not available for shopify"""
    
    update_batch = []
    

    for data in data_list:
        product_info = {}
        product_id = None
        parent_id = None
        sku = data['variation']['sku']
        if data.get('destination') is None or \
        data['destination'].get('destination_product_id') is None:
            exists = search_exist(table_objs.get('destination'), 
                                session, 
                                {'sku': sku,
                                'front_shop_id': shop_connector.front_shop_id,
                                #    'available': True,
                                'is_current_price': True})
            if exists is None or len(exists) == 0:
                logger.info(f"variation sku {sku} not at shop or not available")
                continue
            product_id = exists[0].destination_product_id
            parent_id = exists[0].destination_parent_id
            if data['destination'].get('price') is None:
                data['destination']['price'] = exists[0].price
        else:
            product_id = data['destination']['destination_product_id']
            parent_id = data['destination'].get('destination_parent_id')
        
        product_info.update(data.get('product', {}))
        product_info.update(data.get('variation', {}))
        product_info.update(data.get('destination', {}))
        product_info['id'] = product_id
        product_info['parent_id'] = parent_id
        # print(product_info)
        update_batch.append(product_info)

        if len(update_batch) == batch_size:
            res_shop = shop_connector.update_shop_product_batch(
                    update_batch, **kwargs)
            # print(res_shop)
            #print(f'last update {product_id} ')
            update_batch = []

    if len(update_batch) > 0:
        res_shop = shop_connector.update_shop_product_batch(
                update_batch, **kwargs)
        # print(res_shop)
        print(f'last update {product_id} ')



def update_product_at_front_shop(table_objs, session, shop_connector, 
                                   data, sku, **kwargs):
    if shop_connector.front_shop_id is None:
        get_front_shop_id(table_objs, session, shop_connector)
    product_id = None
    parent_id = None
    product_info = {}
    if data.get('destination') is None or \
    data['destination'].get('destination_product_id') is None:
        exists = search_exist(table_objs.get('destination'), 
                              session, 
                              {'sku': sku,
                               'front_shop_id': shop_connector.front_shop_id,
                            #    'available': True,
                               'is_current_price': True})
        if exists is None or len(exists) == 0:
            logger.info(f"variation sku {sku} not at shop or not available")
            return None
        product_id = exists[0].destination_product_id
        parent_id = exists[0].destination_parent_id
        if data['destination'].get('price') is None:
            data['destination']['price'] = exists[0].price
    else:
        product_id = data['destination']['destination_product_id']
        parent_id = data['destination'].get('destination_parent_id')
    
    product_info.update(data.get('product', {}))
    product_info.update(data.get('variation', {}))
    product_info.update(data.get('destination', {}))
    #update frontshop 
    res = shop_connector.update_shop_product(
                                   product_info, 
                                   str(product_id), 
                                   parent_id=parent_id,
                                   **kwargs)
    logger.debug(f'{product_id}, {sku}')
    return res

def _get_category_by_name(table_obj, session, name):
    exists = search_exist(table_obj, session, {'category': name})
    if exists and len(exists) > 0:
        return {'category_id': exists[0].id}
    new_cat = add_json_to_db(table_obj, session, {'category': name})
    return {'category_id': new_cat['id']}

# def _update_product_at_frontshop_by_sku(table_objs, session, shop_connector, 
#                                           sku:str, data:dict):
#     """search product at frontshop by sku, 
#        if exist, update
#        Unavailable with shopify
#     """
#     product_id = shop_connector.get_destination_product_id(sku)
#     if product_id is not None:
#         return shop_connector.update_shop_product(
#                                    data, 
#                                    str(product_id),
#                                    formated=True)