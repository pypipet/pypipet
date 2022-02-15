import pytest
from pypipet.core.operations.fulfillment import *
from pprint import pprint

from tests.conftest import shop_conn


def test_shipment_info(session, obj_classes,shop_conn):
    ff = get_shipping_info(obj_classes, session, {'destination_order_id': '49455',
                                        'front_shop_id': shop_conn.front_shop_id})
    # pprint(ff)
    ff = get_shipping_info(obj_classes, session, {'shop_order_id': 10})

def test_unfulfilled(session, obj_classes):
    res = get_unfulfilled_order_inprocesss(obj_classes, session)
    assert res is not None
    print(res)
    
def test_add_fulfillment(session, obj_classes,shop_conn):
    ff = [{'destination_order_id': '49455', 
    'front_shop_id': shop_conn.front_shop_id, 
          'provider': 'USPS', 'tracking_id': '1111111'}]
    add_fulfillment_bulk(obj_classes, session, ff)
    ff = [{'shop_order_id': 4, 
          'provider': 'USPS', 'tracking_id': '1111111'}]
    res = add_fulfillment_bulk(obj_classes, session, ff)
    assert res is None


def test_add_fulfillment2(session, obj_classes,shop_conn):
    ff = [{'destination_order_id': '4297439150250', 
    'front_shop_id': shop_conn.front_shop_id, 
          'provider': 'USPS', 'tracking_id': '222222'}]
    add_fulfillment_bulk(obj_classes, session, ff)
    res = get_shipping_info(obj_classes, session, {'destination_order_id': '4297439150250',
                                        'front_shop_id': shop_conn.front_shop_id})
    assert res['tracking_id'] == '222222'

def test_update_fulfillment(session, obj_classes,shop_conn):
    param = {'destination_order_id': '49455', 
    'front_shop_id': shop_conn.front_shop_id} 
    data ={ 'provider': 'fedex,USPS', 'tracking_id': '222,33333'}
    res = update_tracking(obj_classes, session, data, param)
    res = get_shipping_info(obj_classes, session, {'destination_order_id': '49455',
                                        'front_shop_id': shop_conn.front_shop_id})
    assert res['tracking_id'] == '222,33333'

    param = {'shop_order_id':4 } 
    data ={ 'provider': 'USPS', 'tracking_id': '44444'}
    res = update_tracking(obj_classes, session, data, param)
    assert res is None


def test_to_front_shop(session, obj_classes, shop_conn):
    # params = {'shop_order_id':4 } 
    # update_fulfillment_to_front_shop(obj_classes, session, shop_conn, params)

    params = {'destination_order_id': '4297439150250', 
    'front_shop_id': shop_conn.front_shop_id}
    update_fulfillment_to_front_shop(obj_classes, session, shop_conn, params)

def test_to_front_shop(session, obj_classes, shop_conn):
    data = {'destination_order_id': '4297439150250', 
    'front_shop_id': shop_conn.front_shop_id, 
          'provider': 'USPS', 'tracking_id': '1111111'}
    update_fulfillment_to_front_shop(obj_classes, session, shop_conn, {}, 
        tracking_info=data, add_new=False)      