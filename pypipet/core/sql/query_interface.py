"""meta queries interfaces with Database"""
from .query import *
import logging
logger = logging.getLogger('__default__')
logger.setLevel(logging.DEBUG)


def get_server_timestamp(session):
    ts = query_server_timestamp(session)
    if ts:
        return ts[0]

def get_latest_record(table_obj, session, key:str, params: dict=None):
    if params is None: params = {}
    return table_latest_record(table_obj, session, key,filters=params)

def search_exist(table_obj, session, params:dict):
    return  db_select(table_obj,
              session,
              filters=params)

def add_to_db(table_obj, session, obj):
    return db_insert(obj, table_obj, session)

def add_json_to_db(table_obj, session, data):
    res = db_insert_raw(table_obj, session, data)
    if res:
        return _object2dict(res)

def add_to_db_bulk(table_obj, session, objs:list):
    db_insert_bulk(objs, 
                table_obj,
                session)

def raw_query(query, session, params: dict=None):
    if params is None: params = {}
    return db_raw_query(query, session, params)


def add_if_not_exist(table_obj, session, obj, unique_keys:list):
    res = db_select(table_obj, 
                   session, 
                   filters=obj.get_unique_attrs(unique_keys))
    if res and len(res) > 0:
        return res[0]

    return db_insert(obj, table_obj, session)

# def add_json_if_not_exist(table_obj, session, data):
#     res = db_select(table_obj, 
#                    session, 
#                    filters=data)
#     if len(res) > 0:
#         return res[0]
#     print(res)
#     return db_insert_raw(table_obj, session, data)

def update_data(table_obj, session, data:dict, params:dict):
    return db_update(table_obj, session, 
                   data, 
                   filters=params)

def update_bulk(table_obj, session, data:list):
    return db_update_bulk(table_obj, session, data)

def update_if_exit(table_obj, session, obj, unique_keys:list):
    filters = obj.get_unique_attrs(unique_keys)
    res = db_select(table_obj, 
                   session, 
                   filters=filters)
    if len(res) > 0:
        db_update(table_obj, session, 
                   obj.get_all_attrs(), 
                   filters=filters)
        return True 
    return False

def add_destination(table_obj, session, obj, unique_keys:list):
    filters = obj.get_unique_attrs(unique_keys)
    filters.update({
        'is_current_price': True
    })
    res = db_select(table_obj, 
                   session, 
                   filters=filters)
    if len(res) > 0:
        exist = res[0]
        return exist
        
    obj.set_attr('is_current_price', True)
    obj.set_attr('available', True)
    return db_insert(obj, table_obj, session)

def get_destination(table_obj, session, params:dict):
    params.update({
        'is_current_price': True
    })
    res = db_select(table_obj, 
                   session, 
                   filters=params)
    if len(res) == 0:
        return []
    if len(res) > 0:
        exist = [_object2dict(res[0])]
        return exist
    if len(res) > 1 and params.get('front_shop_id') is not None:
        logger.debug(f"sku {params.get('sku')} published multiple time \
        at shop {params['front_shop_id']}")


def update_destination_price(table_obj, session, price, params: dict):
    
    params.update({
         'is_current_price': True
    })
    res = db_select(table_obj, 
                   session, 
                   filters=params)
    if res is None:
        logger.debug(f'query failded {params}')
        return 

    if len(res) == 1:
        data = _object2dict(res[0])
        # print(data)
        #price no change
        if data['price'] == price:
            return res[0]

        db_update(table_obj, session, 
                   {'is_current_price': False}, 
                   filters=params)
        
        if data.get('id'):
            del data['id']
        data.update({
            'price': price,
            'is_current_price': True,
            'available': True
        })
       
        return db_insert_raw(table_obj, session, data)

    if len(res) > 1:
        logger.debug(f'published multiple times at \
                        same destination {params}')

def add_new_product(table_objs, session, product: object):   
    if product.category is not None:
        category = product.category
        unique_keys = list(category.get_all_attrs().keys())
        res = add_if_not_exist(table_objs.get(category.__table_name__), 
                    session, category, unique_keys)
        product.set_attr('category_id', res.id)

    # unique_keys = list(product.get_all_attrs().keys())
    unique_keys = ['identifier']
    res = add_if_not_exist(table_objs.get(product.__table_name__), 
                session, product, unique_keys)
    
    if res is None: return 
    product_id = res.id

    product.update_product_id(product_id)
    
    if len(product.variations) >0:
        variation_table = table_objs.get(product.variations[0].__table_name__)
        new_variations = []
        #check is_duplicate_skus
        for vari in product.variations:
            if _is_duplicate_sku(variation_table, session, vari.sku):
                logger.debug(f'duplicate sku {vari.sku}')
            else:
                new_variations.append(vari)
        db_insert_bulk(new_variations, 
                      variation_table,
                      session)
    return product

def get_product_with_variations(table_objs, session, params: dict, 
                                       include_published=False, front_shop_id=None, include_category=False):
    product_info = None
    if params.get('identifier') is not None:
        product_info = get_product_by_identifier(table_objs, session, 
                                          {'identifier': params['identifier']},
                                          include_category=include_category)
    elif params.get('product_id') is not None:
        product_info = get_product_by_identifier(table_objs, session, 
                                          {'id': params['product_id']},
                                          include_category=include_category) 
    elif params.get('sku') is not None:
        product_info = get_variation_info_by_sku(table_objs, session, params['sku'],
                                                 front_shop_id=front_shop_id)
        if product_info is None:
            logger.debug(f'invalid params {params}')
            return 
        if not include_published and front_shop_id and product_info.get('destinations'):
            publish_status, dest = is_sku_published(product_info.get('destinations'), 
                                params['sku'], front_shop_id)
            logger.debug(f'publish_status: {publish_status}')
            if publish_status == 1:
                return 
            elif publish_status == 2:
                product_info['set_available_flag'] = True
                product_info['destination_id'] = dest['id']
        return product_info

    if product_info is None:
        logger.debug(f'invalid params {params}')
        return 

    product_info = _tranfrom_product(table_objs.get('destination'), session,
                         product_info, front_shop_id, include_published=include_published)
    return product_info


def is_sku_published(dests, sku, front_shop_id):
    """
    return: (status_code, destination)
            status_code:
            0  not added yet
            1  added and available =True 
            2  added and available = False #need update the flag
    """
    for dest in dests:
        if dest['front_shop_id'] == front_shop_id and dest['sku'] == sku:
            if not dest['available']:
                logger.debug(f"sku {sku} has been add to shop {front_shop_id}, \
                need set availability flag as True") 
                return 2, dest
            logger.debug(f"sku {sku} has been add to shop {front_shop_id}") 
            return 1, dest
    return 0, None

def _tranfrom_product(table_obj, session, product_info, front_shop_id, include_published=False):
    """transform product_info depends on if it has multiple variations"""
    if product_info.get('variations') is None:
        return 
    if product_info.get('variations') and len(product_info['variations']) == 1:
        #return simple product dict 
        product_info.update(product_info['variations'][0])
        del product_info['variations'] 
        
        dests = get_destination(table_obj, session, {'sku': product_info['sku'],
                                                    'front_shop_id': front_shop_id})
        if dests is None:
            return
        if include_published:
            product_info['destinations'] = dests
            return product_info

        publish_status, dest = is_sku_published(dests, product_info['sku'], front_shop_id)
        if publish_status == 1:
            return
        elif publish_status == 2:
            product_info['set_available_flag'] = True
            product_info['destination_id'] = dest['id']

        return product_info
    
    parent_id = None
    for i, vari in enumerate(product_info['variations']):
        dests = get_destination(table_obj, session, {'sku': vari['sku'],
                                                    'front_shop_id': front_shop_id})
        
        if dests is None:
            logger.debug(f"destination query error sku {vari['sku']} at shop {front_shop_id}")
            return 
        if include_published:
            product_info['destinations'] = dests
        else:
            publish_status, dest = is_sku_published(dests, vari['sku'], front_shop_id)
            if publish_status == 1:
                product_info['variations'][0]['add_flag'] = True
                product_info['variations'][0]['destination_id'] = dest['id']
            elif publish_status == 2:
                product_info['variations'][0]['set_available_flag'] = True
                product_info['variations'][0]['destination_id'] = dest['id']

            if dest and dest.get('destination_parent_id'):
                parent_id = dest['destination_parent_id']
    if parent_id:
        product_info['parent_id'] = parent_id
    return product_info

# def get_destination_by_sku(table_objs, sku, front_shop_id):
#     params = {'sku': sku, 'is_current_price': True,
#               'front_shop_id': front_shop_id}
#     dests = db_select(table_objs.get('destination'), 
#                    session, 
#                    filters=params)
#     if len(dests) > 0:
#         return _object2dict(dests[0])
#     elif len(dests) > 1:
#         logger.debug(f'sku {sku} published multiple at shop {front_shop_id}')

def get_product_by_identifier(table_objs, session, params:dict, include_category=False):
    product = db_select(table_objs.get('product'), 
                        session, 
                        filters=params)
    if len(product) == 0:
        return None 
    
    product = product[0]
    variations =  db_select(table_objs.get('variation'), 
                   session, 
                   filters={'product_id': product.id})

    product_info = _object2dict(product)

    if include_category:
        category = db_select(table_objs.get('category'), 
                   session, 
                   filters={'id': product_info['category_id']})
        product_info['category'] = category[0].category

    if len(variations) > 0:
        product_info['variations'] = [_object2dict(v) for v in variations]
    
    if product_info.get('id'):
        del product_info['id']
    return product_info

def get_product_by_sku(table_objs, session, sku:str, include_category=False):
    variation = db_select(table_objs.get('variation'), 
                   session, 
                   filters={'sku': sku})
    if len(variation) == 0:
        return None 

    variation = _object2dict(variation[0])

    product = db_select(table_objs.get('product'), 
                   session, 
                   filters={'id': variation['product_id']})
    
    product_info = _object2dict(product[0])
    product_info.update(variation)

    if include_category:
        category = db_select(table_objs.get('category'), 
                   session, 
                   filters={'id': product_info['category_id']})
        product_info['category'] = category[0].category
        product_info['full_category'] = category[0].full_path

    return product_info

def get_product_name_by_sku(table_objs, session, sku:str):
    variation = db_select(table_objs.get('variation'), 
                   session, 
                   filters={'sku': sku})
    if len(variation) == 0:
        return None 

    variation = _object2dict(variation[0])

    product = db_select(table_objs.get('product'), 
                   session, 
                   filters={'id': variation['product_id']})
    
    product_info = _object2dict(product[0])
    product_info.update(variation)


    return product_info


def get_variation_info_by_sku(table_objs, session, sku:str, front_shop_id=None):
    variation = db_select(table_objs.get('variation'), 
                   session, 
                   filters={'sku': sku})
    if len(variation) == 0:
        return None 
   
    variations = db_select(table_objs.get('variation'), 
                   session, 
                   filters={'product_id': variation[0].product_id})
    
    product_info = {}
    
    if len(variations) > 1:
        #multi variation 
        assert front_shop_id is not None
        skus = [v.sku for v in variations]
        parent = get_destination_parent(table_objs.get('destination'), 
                                session, front_shop_id, skus)
        if parent and parent.get('destination_parent_id'):
            product_info['parent_id'] = parent['destination_parent_id']
            product_info['variations'] = [_object2dict(variation[0])] # variation with the sku
        elif parent and parent.get('destination_product_id'):
            #added product with incorrect type
            product_info['parent_id'] = parent['destination_product_id']
            product_info['parent_note'] = 'INCORRECT_TYPE'
            product_info['variations'] = [_object2dict(vari) for vari in variations] 
        elif parent:
            logger.debug(f'invalid parent, sku {sku}')
        else:
            product_info['variations'] = [_object2dict(variation[0])] 

        product_info['product_id'] = variations[0].product_id
        
    else:
        #single variation
        product_info.update(_object2dict(variation[0]))
    
    #variation = _object2dict(variation[0])

    product = db_select(table_objs.get('product'), 
                   session, 
                   filters={'id': product_info['product_id']})
    
    product_info.update(_object2dict(product[0]))
    if product_info.get('id'):
        del product_info['id']
    #variation.update(product_info)

    category = db_select(table_objs.get('category'), 
                   session, 
                   filters={'id': product_info['category_id']})
    product_info['category'] = category[0].category
    # product_info['full_category'] = category[0].full_path
    
    #get existing destination
    params = {'sku': sku, 'is_current_price': True}
    if front_shop_id is not None:
        params['front_shop_id'] = front_shop_id
    dests = db_select(table_objs.get('destination'), 
                   session, 
                   filters=params)
    if len(dests) > 0:
        product_info['destinations'] = [_object2dict(d) for d in dests]

    return product_info

def get_product_by_destination(table_objs, session, params:dict):
    dest = db_select(table_objs.get('destination'), 
                   session, 
                   filters=params)
    if len(dest) == 0:
        return None 
    dest = dest[0]

    variation = db_select(table_objs.get('variation'), 
                   session, 
                   filters={'sku': dest.sku})
    if len(variation) == 0:
        return None 
    variation = variation[0]
    info = _object2dict(variation)

    product = db_select(table_objs.get('product'), 
                   session, 
                   filters={'id': variation.product_id})
    
    if len(product) == 0:
        return None 

    info.update(_object2dict(product[0]))
    return info

def get_order(table_objs, session, params:dict, **kwargs):
    order = db_select(table_objs.get('shop_order'), 
                   session, 
                   filters=params)
    if order is None or len(order) == 0:
        return None 
    order = order[0]
    order_info =  _object2dict(order)

    order_items = db_select(table_objs.get('order_item'), 
                   session, 
                   filters={'shop_order_id': order.id})
    if kwargs.get('item_info') == True:
        item_info =  []
        for d in order_items:
            prods = get_products(table_objs, session, {'sku': d.sku})
            
            item_info.append(prods[0]._asdict())
        
    else:
        order_items =  [_object2dict(d) for d in order_items]

    order_info['order_item'] = item_info

    billing = db_select(table_objs.get('customer'), 
                   session, 
                   filters={'id': order.billing_customer_id})
    if len(billing) > 0:
        order_info['billing_customer'] = _object2dict(billing[0]) 
        if order.billing_customer_id == order.shipping_customer_id:
            order_info['shipping_customer'] = order_info['billing_customer']
        else:
            shipping = db_select(table_objs.get('customer'), 
                   session, 
                   filters={'id': order.shipping_customer_id})
            if len(shipping) > 0:
                order_info['shipping_customer'] = _object2dict(shipping[0]) 
    
    return order_info

def get_filtered_orders(table_objs, session, params:dict, **kwargs):
    orders = filter_order(table_objs, 
                   session, 
                   params,
                   start_id=kwargs.get('start_id'),
                   start_dt=kwargs.get('start_dt'))
    return [r._asdict() for r in orders] 

def aggregate_inventory_qty(table_objs, session, 
                       start_from_sku: str, params={}, 
                       batch_size=10,latest_hours=24):
    # res = get_inventory(table_objs, session, start_from_sku, batch_size,
    #                      params=params, latest_hours=latest_hours)
    res = get_latest_inventory_update(table_objs.get('inventory'), session, start_from_sku, batch_size,
                         params=params, latest_hours=latest_hours)
    if res is not None:
        return [r._asdict() for r in res]

def get_variation_instock_qty(table_objs, session, 
                       start_product_id: str, params={}, 
                       batch_size=10, latest_hours=24):
    res = get_variation_instock(table_objs, session, 
                         start_product_id, 
                         batch_size,
                         params=params,
                         latest_hours=latest_hours)
    
    if res is not None:
        return [r._asdict() for r in res]

# def get_inventory_update_after(table_objs, session, 
#                                     after_dt, params:dict=None):
#     res = get_inventory_update(table_objs, session, after_dt, params)
#     if res is not None:
#         return [r._asdict() for r in res]

def update_inventory(table_obj, session, 
              update_data: dict, params:dict):
    if update_data.get('currency') is None:
        update_data['currency'] = 'USD'
    
    res = db_select(table_obj, 
                   session, 
                   filters=params)
    if res and len(res) > 0:
        db_update(table_obj, session, 
                   update_data, 
                   filters={'id': res[0].id})
        return res[0]
    else:
        update_data.update(params)
        return db_insert_raw(table_obj, session, update_data)

# def get_inventory_by_sku(table_obj, session, sku:str):
#     res = db_sum_query(table_obj, 
#                  session, 
#                  table_obj.qty, 
#                  group_by=[table_obj.sku],
#                  params={'sku': sku})
#     if len(res) > 0:
#         return res[0]._asdict().get('sum')
def get_variation_instock_by_skus(session, front_shop_id, skus: list):
    return get_instock_by_skus(session, front_shop_id, skus)

def get_fulfilled_orders(table_objs, session, status='processing', 
                           shop_order_id_list=None, params:dict=None):
    if params is None: params = {}
    if shop_order_id_list is None:
        ff = get_fulfilled_order_in_processing(table_objs, session, status=status, params=params)
        return [r._asdict() for r in ff]
    elif type(shop_order_id_list) is list:
        ff = get_fulfilled_order_in_processing(table_objs, session, status=status, params={
            'shop_order_id_list': shop_order_id_list
        })
        return ff
    else:
        logger.debug('invalid parmas')
        return []

def get_front_shop(table_obj, session, url:str=None, name:str=None):
    if name:
        res = db_select(table_obj, 
                   session, 
                   filters={'name': name})
        if len(res) > 0:
            return res[0] 

    if url:
        res = db_select(table_obj, 
                   session, 
                   filters={'url': url})
        if len(res) > 0:
            return res[0]  

def insert_list_raw(table_obj, session, data: list):
    """table_obj: sqlalchemy.ext.automap
       data: list of dict"""    
    for d in data:
        db_insert_raw(table_obj, session, d)

def _is_duplicate_sku(table_obj, session, sku):
    res = db_select(table_obj, session, filters={'sku': sku})
    if len(res) > 0:
        return True 

    return False

def _object2dict(table_obj):
    d = {}
    for k in table_obj.__table__.columns.keys():
        d[k] = table_obj.__dict__.get(k, None)
    return d