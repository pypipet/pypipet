"""woocommerce version 5.5.2"""
from .utility import *
import logging
from copy import deepcopy

def exception_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except  TypeError as e:
            logging.debug(e)
    return wrapper



@exception_handler
def wp_parse_order(data:dict, attr_mapping: dict, 
                      shipping_tax_id: int, item_tax_id:int):
    """to do: meta data of other payment mehods"""
    order_data = {}
    if attr_mapping.get('shop_order'):
        field_mapping(data, order_data, attr_mapping['shop_order'])
        if order_data.get('refund') and order_data['refund'] is not None:
            order_data['refund'] = abs(order_data['refund'])
            order_data['order_total'] -= order_data['refund'] 

    # manual input attr value
    order_data['shipping_tax_id'] = shipping_tax_id

    order_data['order_item'] = []
    for item in data['line_items']:
        order_item = {}
        field_mapping(item, order_item, attr_mapping['order_item'])
        order_item['tax_id'] = item_tax_id
        #for variations
        if item.get('variation_id'):
            order_item['destination_product_id'] = str(item['variation_id'])
        order_data['order_item'].append(order_item)
    
    #billing
    order_data['billing_customer'] = {}
    field_mapping(data['billing'], 
                  order_data['billing_customer'], 
                  attr_mapping['customer'])
    order_data['billing_customer']['is_billing'] = True
    #shipping
    if data['shipping']['first_name'].strip() != '' \
    and data['shipping']['last_name'].strip() != '':
        if data['billing']['first_name'] == data['shipping']['first_name'] \
        and data['billing']['last_name'] == data['shipping']['last_name'] \
        and data['billing']['address_1'] == data['shipping']['address_1'] \
        and data['billing']['postcode'] == data['shipping']['postcode'] :
            order_data['shipping_customer'] = order_data['billing_customer']
            order_data['billing_customer']['is_shipping'] = True
        else:
            order_data['shipping_customer'] = {}
            field_mapping(data['shipping'], order_data['shipping_customer'], 
                            attr_mapping['customer'])
            order_data['shipping_customer']['is_shipping'] = True
    else:
        order_data['shipping_customer'] = order_data['billing_customer']
        order_data['billing_customer']['is_shipping'] = True
    
    return order_data



def wp_category_to_taxonomy(cats):
    cat_map = {}
    for c in cats:
        if cat_map.get(c['id']) is None:
            cat_map[c['id']] = {'name': c['name'],  'parent_id': c['parent']}

    for i, c in enumerate(cats):
        parent = None
        full_path = None
        if c['parent'] != 0 and cat_map.get(c['parent']):
            parent =  cat_map[c['parent']]['name']
        
        full_path = _get_full_path(c['id'], cat_map)
        
        cats[i] = {
            'category': c['name'],
            'parent': parent,
            'full_path': full_path
        }


def _get_full_path(category_id, category_map):
    parent_id = category_id
    path_nodes  = []
    while True:
        if parent_id == 0: break
        parent = category_map.get(parent_id, None)
        if parent is None: break
        
        path_nodes.insert(0, parent['name'])
        parent_id = parent['parent_id']
    return '>'.join(path_nodes)

@exception_handler
def parse_product(data:dict, attr_mapping):
    if data is None: return 
    if data.get('parent_id') and type(data['parent_id']) is int:
        #is variations 
        return 0
    if data.get('variations') and len(data['variations']) > 0:
        # is parent
        return 1

    res = {}
    product = {}
    if attr_mapping.get('product'):
        field_mapping(data, product, attr_mapping['product'])
    
    if attr_mapping.get('variation'):
        variation = {}
        field_mapping(data, variation, attr_mapping['variation'])
        if variation.get('sku') is None or variation['sku'].strip() == '':
            variation['sku'] = str(data['id'])
        product['variations'] = [variation]

    res['product'] = product
     
    if attr_mapping.get('destination'):
        dest = {}
        field_mapping(data, dest, attr_mapping['destination'])
        if dest.get('sku') is None or dest['sku'].strip() == '':
            dest['sku'] = str(data['id'])
        res['destinations'] = [dest]
   

    if attr_mapping.get('inventory') and data['manage_stock'] == True:
        inv= {}
        field_mapping(data, inv, attr_mapping['inventory'])
        res['inventory'] = inv 
    return res


@exception_handler
def parse_product_with_variations(data:dict, attr_mapping):
    res = {}
    product = {}
    if attr_mapping.get('product'):
        field_mapping(data, product, attr_mapping['product'])

    default_variation = {}
    field_mapping(data, default_variation, attr_mapping['variation'])
    
    product['variations'] = []
    dests = []
    invs = []
    
    for vari in data['variations']:
        vari_info = deepcopy(default_variation)
        field_mapping(vari, vari_info, attr_mapping['variation_attrs'])
        
        vari_info['images'] = ','.join([vari_info['images'],default_variation['images']])
        vari_info['description'] = default_variation['description'] + '\n' \
                                   + vari_info['description']
        if vari.get('sku') is None or vari['sku'].strip() == '':
            vari_info['sku'] = str(data['id'])
        
        product['variations'].append(vari_info)

        dest = {'destination_parent_id': str(data['id'])}
        field_mapping(vari, dest, attr_mapping['destination'])
        if dest.get('sku') is None or dest['sku'].strip() == '':
            dest['sku'] = str(data['id'])
        dests.append(dest)

        inv= {}
        field_mapping(vari, inv, attr_mapping['inventory'])
        invs.append(inv)
   
    res = {
        'product': product,
        'destinations': dests,
        'inventory': invs
    }

    return res
