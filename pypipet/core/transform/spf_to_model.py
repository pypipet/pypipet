"""shopify version 2022-01"""
from builtins import isinstance
from .utility import *
import logging

def exception_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except  TypeError as e:
            logging.debug(e)
    return wrapper



@exception_handler
def parse_order(data, attr_mapping,shipping_tax_id=None, item_tax_id=None, **kwargs):
    if data is None: return 
    order_data = {}
    if attr_mapping.get('shop_order'):
        field_mapping(data, order_data, attr_mapping['shop_order'])
        if data.get('cancelled_at') is not None:
            order_data['status'] = 'cancelled'
    if shipping_tax_id:
        order_data['shipping_tax_id'] = shipping_tax_id

    order_data['order_item'] = []
    for item in data['line_items']:
        order_item = {}
        field_mapping(item, order_item, attr_mapping['order_item'])
        if item_tax_id:
            order_item['tax_id'] = item_tax_id
        order_data['order_item'].append(order_item)

    order_data['billing_customer'] ={'email': data.get('email'),
                                    'phone': data.get('phone'),
                                    'is_billing': True}
    if data.get('billing_address'):
        field_mapping(data['billing_address'], 
                  order_data['billing_customer'], 
                  attr_mapping['customer'])
    
    if data.get('shipping_address'):
        if data.get('billing_address') and data['shipping_address']['first_name'].strip() != '' \
    and data['shipping_address']['last_name'].strip() != '':
            if data['billing_address']['first_name'] == data['shipping_address']['first_name'] \
            and data['billing_address']['last_name'] == data['shipping_address']['last_name'] \
            and data['billing_address']['address1'] == data['shipping_address']['address1'] \
            and data['billing_address']['zip'] == data['shipping_address']['zip'] :
                order_data['shipping_customer'] = order_data['billing_customer']
                order_data['billing_customer']['is_shipping'] = True
            else:
                order_data['shipping_customer'] = {}
                field_mapping(data['shipping_address'], order_data['shipping_customer'], 
                                attr_mapping['customer'])
                order_data['shipping_customer']['is_shipping'] = True
        else:
            order_data['shipping_customer'] = order_data['billing_customer']
            order_data['billing_customer']['is_shipping'] = True

    if data.get('fulfillments') and len(data['fulfillments']) > 0 and attr_mapping.get('fulfillment'):
        order_data['fulfillment'] = []
        for ff_info in data['fulfillments']:
            if ff_info.get('status') != 'success': continue
            ff_info['status'] = 'shipped'  # mapped to shipped
            ff = {'destination_order_id': str(data['id'])}
            field_mapping(ff_info, 
                  ff, 
                  attr_mapping['fulfillment'])
            if ff.get('tracking_id') and isinstance(ff['tracking_id'], list):
                ff['tracking_id'] = ','.join(ff['tracking_id'])
            order_data['fulfillment'].append(ff)
    return order_data

@exception_handler
def parse_product(data: dict, attr_mapping):
    if data is None: return 

    res = {}
    product = {}
    options = []
    if attr_mapping.get('product'):
        field_mapping(data, product, attr_mapping['product'])
        if product.get('category') is None:
            product['category'] = 'undefined'
        options = [opt['name'] for opt in data['options']]
    
    if attr_mapping.get('variation'):
        product['variations'] = []
        for vari in data.get('variants'):
            variation = {}
            vari.update({ 'images': data['images'],
                          'meta': vari.get('meta',[]) + data.get('meta',[])})
            field_mapping(vari, variation, attr_mapping['variation'])
            if variation.get('sku') is None or variation['sku'].strip() == '':
                variation['sku'] = str(vari['id'])
            variation['description'] = f"{data['body_html']} - {variation['description']}"
            #options: shopfy has max 3 options
            for i in range(1,4):
                if vari.get(f'option{i}') is not None and i <= len(options):
                    variation[options[i-1]] = vari[f'option{i}']

            product['variations'].append(variation)

    res['product'] = product
     
    if attr_mapping.get('destination'):
        res['destinations'] = []
        for vari in data.get('variants'):
            dest = {}
            vari.update({'parent_id': data['id']})
            field_mapping(vari, dest, attr_mapping['destination'])
            if dest.get('sku') is None or dest['sku'].strip() == '':
                dest['sku'] = str(vari['id'])
            if dest.get('discount'):
                dest['discount']  -=  dest['price']
                if dest['discount'] > 0:
                    dest['price'] += dest['discount'] 
            res['destinations'].append(dest)
   

    return res



