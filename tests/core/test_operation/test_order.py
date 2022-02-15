import pytest
from pypipet.core.operations.order import *
from pypipet.core.model.order import Order
from pprint import pprint


def test_get_order(obj_classes, session,shop_conn):
    res = get_order_from_shop_by_id('4296279752874', shop_conn)
    
    # res = get_orders_from_shop(obj_classes, session, shop_conn)
    pprint(res)

@pytest.fixture()
def shop_order(session, shop_conn, obj_classes):
    res = get_orders_from_shop(obj_classes, session, shop_conn)
    assert res is not None 
    if len(res) > 0:
        res = get_order_from_shop_by_id(res[-1]['destination_order_id'], shop_conn)
        pprint(res)
        return res

def test_import_order(session, shop_conn, obj_classes, shop_order):
    if shop_order:
        add_orders_to_db_bulk(obj_classes, session, [shop_order], 
                           shop_conn.front_shop_id)


def test_import_order_by_id(session, shop_conn, obj_classes):
    order_id = '4297439150250'
    res = get_order_from_shop_by_id(order_id, shop_conn)
    pprint(res)
    order_obj = Order()
    order_obj.set_order(obj_classes, res)
    add_order_to_db(obj_classes, session, order_obj, shop_conn.front_shop_id)

def test_update_customer(session, obj_classes, shop_conn):
    update = {'email': 'Bdom@aidom.ca',  'postcode': 'v8j 4v7'}
    order = get_order_info(obj_classes, session, 
                                 {'destination_order_id':'4296601993386', 
                                   'front_shop_id':shop_conn.front_shop_id})
    shipping_customer_id = order['shipping_customer']['id']
    res = update_customer_to_db(obj_classes.get('customer'), 
                     session, update, id=shipping_customer_id)
    
    print(res)
    if update.get('id'): del update['id']
    res = update_customer_to_shop(session, shop_conn, update, 
                order['destination_order_id'], is_billing=True,is_shipping=True)

def test_update_order(session, obj_classes,shop_conn):
    update ={'id': 1, 'status': 'cancelled'}
    res = update_order_to_db(obj_classes.get('shop_order'), session, update)
    
    
    update ={'destination_order_id': '49455', 
            'front_shop_id': shop_conn.front_shop_id, 
            'status': 'pending'}
    res = update_order_to_db(obj_classes.get('shop_order'), session, update)
    
    

def test_update_order_item(session, shop_conn, obj_classes):
    sync_order_change_from_shop(obj_classes, session, shop_conn, '4297439150250')

def test_update_order_item_to_shop(session, shop_conn, obj_classes):
    items = [{'destination_product_id':'42501446238378', 'qty': 1, 'price': 99.0}]
    res = update_order_item_to_shop( shop_conn, '4297439150250', items)
    print(res)

    order = get_order_from_shop_by_id( '4297439150250', 
                                   shop_conn)
    pprint(order)

def test_message(shop_conn):
    messge = 'test messgae'
    send_message_to_customer(shop_conn,
                            destination_order_id=49455,
                            message='test message')