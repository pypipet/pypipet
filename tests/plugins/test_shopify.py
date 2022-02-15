import pytest
from pypipet.core.project_context import PipetContext
from pypipet.core.shop_conn.spf import *
from pypipet.core.transform.model_to_spf import (
       product_parser,
       add_metafields,
       transform_imgs,
       variant_parser)
from pprint import pprint
import shopify

variants =[{
    'barcode':'34524t',
    'sku': 'skuafwete',
    'weight': 0.1,
    "weight_unit": "lb",
    'inventory_management':'shopify',
    'price': 45,
    'qty': 10,
    'attributes': {'color': 'red', 'size': '8', 
             'is_package': True, 'has_battery': True},
    'images': 'https://i0.wp.com/ctchealth.ca/wp-content/uploads/2021/11/163985.jpg?fit=633%2C1024&ssl=1'

},
{
    'barcode':'rt6354',
    'sku': 'sku456432',
    'weight': 0.1,
    "weight_unit": "lb",
    'inventory_management':'shopify',
    'price': 90,
    'qty': 19,
    'attributes': {'color': 'black', 'size': '10', 
             'is_package': False, 'has_battery': False},
    'images': 'https://i0.wp.com/ctchealth.ca/wp-content/uploads/2021/04/77731334-1.jpg?fit=960%2C960&ssl=1'

}
]

product = {
    'body_html':'test description',
    'title': 'api product from pypipet',
    'options': [{'name':'color'},{'name':'size'}],
    'category': 'shoes',#category,
    'tags': 't1, t2',
    'vendor': 'self',
    'variants': variants,
    'attributes': {'material': 'plastic'}
}

extra_variant = {
    'barcode':'5463456',
    'sku': 'ae94wwe644',
    'weight': 1.1,
    "weight_unit": "lb",
    'inventory_management':'shopify',
    'price': 39,
    'attributes': {'color': 'black-white', 'size': '6', 
             'is_package': False, 'has_battery': False},
    'images': 'https://i0.wp.com/ctchealth.ca/wp-content/uploads/2021/04/166535216-1.png?w=403&ssl=1'
}

ff_info ={"location_id":66061795498,
            "tracking_numbers":["12333456789"],
            "tracking_urls":["https://tracking.com/?abc"],
            "tracking_company": 'TBD',
            "notify_customer":False}

def test_shop_conn_config(shop_conn):
    assert shop_conn is not None 
    assert shop_conn.front_shop_id is not None 
    assert shop_conn.field_mapping is not None 
    pprint(shop_conn.field_mapping)

def test_parser(ctx):
    variation_imgs  = product_parser(product, ctx.config.get('variation_attrs'))
    pprint(product)
    pprint(variation_imgs)

def test_get_product(shop_conn):
    shopify.ShopifyResource.activate_session(shop_conn.shop_api)
    res = find_product()
    pprint(res)
    shopify.ShopifyResource.clear_session()

def test_get_all_product(shop_conn):
    shopify.ShopifyResource.activate_session(shop_conn.shop_api)
    res = get_all_products(fields='id')
    pprint(res)
    shopify.ShopifyResource.clear_session()

def test_add_product(ctx, shop_conn):
    shopify.ShopifyResource.activate_session(shop_conn.shop_api)

    variation_imgs  = product_parser(product, ctx.config.get('variation_attrs'))
    msg, suc = add_product(product, variant_imgs=variation_imgs)
    assert suc
    print(msg['id'])

    shopify.ShopifyResource.clear_session()

def test_add_to_collection(ctx, shop_conn):
    shopify.ShopifyResource.activate_session(shop_conn.shop_api)
    categories = get_collection_map()
    cid = None
    if categories.get(product['category']) is not None:
        cid = categories[product['category']]
    else:
        cid = add_collection({'title': product['category']})

    res = add_product_to_collection(7216912105642, cid)
    print(res)
    shopify.ShopifyResource.clear_session()

def test_update_inventory(shop_conn):
    shopify.ShopifyResource.activate_session(shop_conn.shop_api)
    info = find_variation('42459697709226')
    res = update_inventory_level(
        info['inventory_item_id'], {'qty':14})
    print(res)
        
    shopify.ShopifyResource.clear_session()

def test_add_variant(ctx, shop_conn):
    shopify.ShopifyResource.activate_session(shop_conn.shop_api)
    variant_parser(extra_variant,  ctx.config.get('variation_attrs'))
    
    msg, suc = add_variation('7216912105642', extra_variant)
    assert suc 
    print(msg)
    print(suc)
    shopify.ShopifyResource.clear_session()

def test_get_order(shop_conn):
    shopify.ShopifyResource.activate_session(shop_conn.shop_api)
    res = get_all_orders(status='open', fields='id,number')
    pprint(res)
    shopify.ShopifyResource.clear_session()

def test_add_tracking(shop_conn):
    shopify.ShopifyResource.activate_session(shop_conn.shop_api)
    res = update_fulfillment_tracking('4288512000170', ff_info)
    pprint(res)
    shopify.ShopifyResource.clear_session()

def test_cancel_order(shop_conn):
    shopify.ShopifyResource.activate_session(shop_conn.shop_api)
    res = update_order_status('4288525598890', 'cancel')
    print(res)
    shopify.ShopifyResource.clear_session()