"""woocommerce version 5.5.2"""

import logging
logger = logging.getLogger('__default__')

from pypipet.core.shop_conn.wc import transform_imgs, transform_category, transform_attrs, transform_attrs_variations

_DEBUG_ = False

def exception_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except  TypeError as e:
            logger.debug(e)
    return wrapper


def parse_to_wp_product_variable(shop_api, product_info: dict, attr_list,
                        variation_attrs: list, update_only=False, parent_id=None):
    if product_info.get('variations') is None \
    or len(product_info['variations']) == 0:
        return  
    
    addtional_attrs = {}
    if product_info.get('brand'): addtional_attrs['brand'] = product_info['brand']
    attrs = transform_attrs_variations(shop_api, attr_list, 
                               product_info['variations'], variation_attrs, 
                               addtional_attrs=addtional_attrs)
    
    parent_product = {'name': product_info['product_name'],
                    'short_description': product_info['short_description'],
                    'type': 'variable',
                    'attributes': attrs,
                    'default_attributes': product_info['variations'][0]['attributes'],
                    'description': product_info['variations'][0]['description'],
                    # 'category': product_info['category']
                    }
    if product_info.get('parent_note') is not None:
        parent_product['parent_note'] = product_info['parent_note']
        
    if parent_product.get('attributes') is not None \
    and len(parent_product['attributes']) == 0:
        del parent_product['attributes']
    if parent_product.get('default_attributes') is not None and \
    len(parent_product['default_attributes']) == 0:
        del parent_product['default_attributes']
    # if product_info.get('category'):
    #     parent_product['category'] = product_info['category']
    
    all_images = []
    for vari in product_info['variations']:
        if vari.get('images'):
            imgs = transform_imgs(vari['images'])
            all_images += imgs
            vari['image'] = imgs[0]
            # del vari['images']
        if vari.get('sub_title'):
            vari['description'] = f"sku {vari['sku']} {vari['sub_title']}"
            del vari['sub_title']

    
    if _DEBUG_: parent_product['images'] = all_images[:2]

    if parent_id is None and not parse_to_wp_product(shop_api, parent_product, 
                                          attr_list, product_type='variable', 
                                          update_only=False, is_variation=False):
        return 

    for i, vari in enumerate(product_info['variations']):
        parse_to_wp_product(shop_api, vari, attr_list, product_type='variable', 
                                          update_only=False, is_variation=True)
        if vari.get('images'): del vari['images']                                  
        product_info['variations'][i] = vari
    
    return {'parent': parent_product, 'variations': product_info['variations']}
        
    # return attrs, product_info['variations']
   
def parse_to_wp_product(shop_api, product_info: dict, attr_list, product_type='simple', 
                                   status='publish',  update_only=False, is_variation=False):
    if not _validate_product_info(product_info, 
                        is_parent=product_type=='variable' and not is_variation,
                        update_only=update_only): 
        return False
        
    if not is_variation and product_type != 'variable':
        product_info['attributes']  = transform_attrs(shop_api, 
                                                    attr_list, 
                                                    product_info)
    else:
        for attr in attr_list:
            if product_info.get(attr): del product_info[attr]

    if product_info.get('attributes') is not None \
    and len(product_info['attributes']) == 0:
        del product_info['attributes']

    if product_info.get('product_name') is not None:
        product_info['name'] = product_info['product_name']
        del product_info['product_name']
    
    if product_info.get('discount') is not None :
        if product_info['discount'] == 0:
            product_info['sale_price'] = ''
        else:
            product_info['sale_price'] = product_info['price'] \
                                            - float(product_info['discount'])
                                           
    if product_info.get('price') is not None:
        product_info['regular_price'] = str(round(float(product_info['price']),2))
        del product_info['price']
    
    if product_info.get('images') and not is_variation and product_type != 'variable':
        product_info['images'] =  transform_imgs(product_info['images'])
        if _DEBUG_: product_info['images'] = product_info['images'][:2]

    if product_info.get('category') is not None:
        product_info['categories'] = [transform_category(shop_api, 
                                            product_info['category'])]
        del product_info['category']

    if product_info.get('weight') is not None:
        product_info['weight'] = str(product_info['weight'])

    if product_info.get('length') is not None and product_info.get('width') \
        is not None and product_info.get('height') is not None:
            _transform_dimension(product_info)
    
    if not update_only:
        if not is_variation:
            product_info.update({
                'type': product_type,
                'status': status
            })
        else:
            if product_info.get('product_id'):
                del product_info['product_id']
        if product_info.get('id') is not None:
            del product_info['id']
    else:
        if product_info.get('product_id') is not None:
            product_info['id'] = int(product_info['product_id'])
            del product_info['product_id']
  
    
    if product_info.get('available') is not None\
    and product_info['available'] == False:
        product_info['in_stock'] = 0

    if product_info.get('in_stock') is not None:
        product_info.update(transform_inventory(product_info['in_stock']))
        del product_info['in_stock']

    if product_info.get('qty') is not None:
        product_info.update(transform_inventory(product_info['qty']))
        del product_info['qty']

    if product_info.get('updated_at') is not None:
        del product_info['updated_at']
    if product_info.get('created_at') is not None:
        del product_info['created_at']
    
    return True


def transform_inventory(qty: int):
    inv = {
         'manage_stock': True,
         'stock_quantity': qty,
    }
    if qty == 0:
        inv['stock_status'] = 'outofstock'
    else:
        inv['stock_status'] = 'instock'
    # print(inv)
    return inv



def transform_customer(data):
    if data.get('address1') is not None:
        data['addres_1'] = data['address1']
    if data.get('address2') is not None:
        data['addres_2'] = data['address2']
    if data.get('updated_at') is not None:
        del data['updated_at']
    if data.get('created_at') is not None:
        del data['created_at']

def transform_order_item(order:dict, items:dict):
    if order.get('line_items') is None:
        return 
    
    item_list = []
    for item in order['line_items']:
        product_key = None
        if item.get('variation_id'):
            product_key = str(item['variation_id'])
        else:
            product_key = str(item['product_id'])
        
        if items.get(product_key) is None:
            continue
        
        if items[product_key].get('qty'):
            item['quantity'] = items[product_key]['qty']
        elif items[product_key].get('order_qty'):
            item['quantity'] = items[product_key]['order_qty']
        elif items[product_key].get('ship_qty'):
            item['quantity'] = items[product_key]['ship_qty']

        item['subtotal'] = str(round(items[product_key]['price']\
            *item['quantity'], 2)) 
        item['total'] = float(item['subtotal']) + float(item['total_tax'])
        item['total'] = str(round(item['total'], 2)) 
        # print(item)
        item_list.append(item)

    return item_list
        

def _validate_product_info(product_info, is_parent=False, update_only=False):
    if not update_only and product_info.get('images') is None:
        logger.debug('missing images info')
        return False

    # if product_info.get('price') is None:
    #     logger.debug('missing price info')
    #     return False

    if not update_only and not is_parent and product_info.get('sku') is None:
        logger.debug('missing sku info')
        return False

    return True

def _transform_dimension(product_info):
    product_info['dimensions'] =  {
        'length': str(product_info['length']),
        'width': str(product_info['width']),
        'height': str(product_info['height'])
    }

