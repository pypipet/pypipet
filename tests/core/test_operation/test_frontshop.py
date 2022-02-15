import pytest
from pypipet.core.operations.frontshop import *
from pprint import pprint
from pypipet.core.transform.wc_to_model import parse_product_with_variations
from pprint import pprint

# def test_product_parser(session, shop_conn, obj_classes, ctx):
#     res = get_product_info(obj_classes, session, shop_conn,sku='W22333995',
#                include_category=True)
#     res['brand'] = 'new brand'
#     res = add_product_to_shop(obj_classes, session, shop_conn, res, 
#                   price=1.0, attr_list=ctx.config.get('attr_list'),
#                   variation_attrs=ctx.config.get('variation_attrs'))
#     # pprint(res)

def test_import_taxonomy(session, shop_conn, obj_classes):
    add_taxonomy_to_db(obj_classes.get('category'), session, shop_conn)

def test_get_products(session, shop_conn, obj_classes):
    product_id= '42501446238378'
    res = get_product_from_shop( shop_conn, product_id, 
                           parent_id='7231132663978', include_meta=True)
    pprint(res)
    # add_product_with_variations_to_db(obj_classes, session, shop_conn, res)

def test_sync_products(session, shop_conn, obj_classes):
    load_products_from_shop(obj_classes, session, shop_conn, 
                         start_from=1, currency='USD',include_meta=True )

def test_sync_product_variation(session, shop_conn, obj_classes):
    product_id= '42426'
    res = get_product_from_shop( shop_conn, product_id)
    # pprint(res)
    add_product_with_variations_to_db(obj_classes, session, shop_conn, res)
  

@pytest.fixture()
def with_variations(session, shop_conn, obj_classes):
    p = get_test_data_variations()
    add_product_to_db(obj_classes, session, p)
    
    res = get_product_info(obj_classes, session, shop_conn,identifier='lwoewnt3',
               include_category=True)
    if res is None:
        res = get_product_info(obj_classes, session, shop_conn,identifier='lwoewnt3', 
                           include_category=True,  include_published=True)
    assert len(res['variations']) > 1
    return res

@pytest.fixture()
def without_variations(session, shop_conn, obj_classes):
    p = get_test_data()
    add_product_to_db(obj_classes, session, p)
    res = get_product_info(obj_classes, session, shop_conn,sku='s27ew89',
               include_category=True)
    if res is None:
        res = get_product_info(obj_classes, session, shop_conn,sku='s27ew89', 
                   include_category=True, include_published=True )
    
    assert res['sku'] is not None
    assert res.get('variations') is None 
    return res
    
def test_add_product_to_shop(ctx, session, shop_conn, obj_classes, without_variations):
    if shop_conn.shop_type == 'shopify':
        res = add_product_to_shop(obj_classes, session, shop_conn, without_variations, 
                  price=1.0, attr_list=ctx.config.get('attr_list'),
                  variation_attrs=ctx.config.get('variation_attrs'))
    else:
        res = add_product_to_shop(obj_classes, session, shop_conn, without_variations, 
                    price=1.0, attr_list=ctx.config.get('attr_list'))
    res = get_product_info(obj_classes, session, shop_conn,
                 sku=without_variations['sku'], include_published=True)
    # assert res.get('destinations') is not None
    pprint(res)

def test_add_product_by_sku(ctx, session, shop_conn, obj_classes):
    sku = 's2789'
    p = get_product_info(obj_classes, session, shop_conn,sku=sku,
               include_category=True, include_published=True)
    
    res = None
    if shop_conn.shop_type == 'shopify':
        res = add_product_to_shop(obj_classes, session, shop_conn, p, 
                  price=1.0, attr_list=ctx.config.get('attr_list'),
                  variation_attrs=ctx.config.get('variation_attrs'),
                  update_inventory=True)
    else:
        res = add_product_to_shop(obj_classes, session, shop_conn, p, 
                    price=1.0, attr_list=ctx.config.get('attr_list'))
    res = get_product_info(obj_classes, session, shop_conn,
                 sku=sku, include_published=True)
    assert res.get('destinations') is not None
    pprint(res)

def test_add_product_to_shop_variations(ctx, session, shop_conn, obj_classes, with_variations):
    res = add_product_to_shop(obj_classes, session, shop_conn, with_variations, 
                  price=1.0, attr_list=ctx.config.get('attr_list'),
                  variation_attrs=ctx.config.get('variation_attrs'))
    res = get_product_info(obj_classes, session, shop_conn,
                 identifier=with_variations['identifier'], include_published=True)
    
    assert res.get('destinations') is not None

def test_add_second_variation(ctx, session, shop_conn, obj_classes):
    p = get_test_data()
    p['variations'].append({
        'sku': 'ere55',
        'color': 'white',
        'description': 'variation',
        'upc': '487432133',
        'images': 'https://m.media-amazon.com/images/I/71br624-J4L._AC_SL1500_.jpg'
    })
    add_product_to_db(obj_classes, session, p)
    sku = 'ere55' #sku from db
    price = 20
    res = add_variation_to_shop(obj_classes, session, shop_conn, 
                  sku, price, attr_list=ctx.config.get('attr_list'),
                  variation_attrs=ctx.config.get('variation_attrs'))
    pprint(res)

def test_add_second_variation2(ctx, session, shop_conn, obj_classes):
    p = get_test_data_variations()
    p['variations'].append({
        'sku': 'test123',
        'color': 'blue-grey',
        'description': 'variation22',
        'price': 11,
        'upc': '487432ee133',
        'images': 'https://m.media-amazon.com/images/I/71br624-J4L._AC_SL1500_.jpg'
    })
    add_product_to_db(obj_classes, session, p)
    sku = 'test123' #sku from db
    price = 20
    res = add_variation_to_shop(obj_classes, session, shop_conn, 
                  sku, price, attr_list=ctx.config.get('attr_list'),
                  variation_attrs=ctx.config.get('variation_attrs'))
    pprint(res)

def test_update_price(ctx, session, shop_conn, obj_classes):
    update = [
        {'sku': 's22123', 'price': 199},
        {'sku': 's2789',  'price': 98}
    ]
    res = update_front_shop_price_bulk(obj_classes, session, shop_conn, update)
    pprint(res)

def test_update_product(ctx, session, shop_conn, obj_classes):
    
    update_product_at_front_shop(obj_classes, session, shop_conn, 
                                   {'destination': {'discount': 5.0}}, 's2789')
    update_destination_to_db(obj_classes.get('destination'), session,
                                   {'discount': 5.0, 'sku':'s2789'}, 
                                    shop_conn.front_shop_id)
    # update_product_at_front_shop(obj_classes, session, shop_conn, 
    #                                {'destination': {'discount': 5.0}}, 's22123')
    # update_destination_to_db(obj_classes.get('destination'), session,
    #                                {'discount': 5.0, 'sku':'s22123'}, 
    #                                 shop_conn.front_shop_id)

def test_update_product_availability(ctx, session, shop_conn, obj_classes):
    
    update_product_at_front_shop(obj_classes, session, shop_conn, 
                                   {'destination': {'available': True,
                                    'in_stock': 10}}, 's2789')
    update_destination_to_db(obj_classes.get('destination'), session,
                                   {'available': True, 'sku':'s2789'}, 
                                    shop_conn.front_shop_id)

def test_update_product_at_shop_bulk(ctx, session, shop_conn, obj_classes):  
    """bulk update not available at shopify"""              
    update = [
        {'variation': {'sku': 's2123'}, 'destination': {'discount': 5.0}},
        {'variation': {'sku': 's2789'},  'destination': {'discount': 5.0}}
    ]
    update_product_at_front_shop_bulk(obj_classes, session, shop_conn, update)
    

def test_update_product_db(ctx, session, obj_classes):
    update = {'brand': 'NA2311', 'identifier': '6245fdr'}
    update_product_to_db(obj_classes, session, update)

def test_update_variation_db(ctx, session, obj_classes):
    update = {'color': 'red and white', 'sku': 's2789'}
    update_variation_to_db(obj_classes.get('variation'), session, update)

def test_update_destination_db(ctx, session, obj_classes,shop_conn):
    update = {'discount': 10, 'sku': 's2789'}
    update_destination_to_db(obj_classes.get('destination'), session, update,
                            shop_conn.front_shop_id)


def get_test_data_variations():
    return {
        'product_name': 'test product name',
        'category': 'test category',
        'identifier': 'lwoewnt3',
        'variations': [
            {'sku': 's22123',
            'color': 'red',
            'description': 'variation 1',
            'upc': '995059',
            'images': 'https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png'},
            {'sku': 's22456',
            'color': 'white',
            'description': 'variation 2',
            'upc': '9348886',
            'images': 'https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png'}
        ]
    } 

def get_test_data():
    return {
        'product_name': 'test product name changed frontshop',
        'category': 'test category',
        'identifier': '6245ewewfdr',
        'variations': [
            {'sku': 's27ew89',
            'color': 'red',
            'description': 'variation',
            'upc': '487434543213',
            'images': 'https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png'}
        ]
    } 