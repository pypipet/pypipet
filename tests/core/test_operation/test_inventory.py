# from pipet.core.sql.query_interface import *
from pypipet.core.operations.inventory import *
import pytest
from pprint import pprint

_supplie_id = 1

def test_update_invs(session, obj_classes, shop_conn):
    invs = [ {'sku':'s22456',  'supplier_id':_supplie_id, 'qty':20}]
    update_inventory_bulk(obj_classes, session, 
                              invs, ignore_new=False)

    res = get_inventory_by_sku(obj_classes, session, 
                            invs[0]['sku'], by_supplier=False)
    pprint(res)

# def test_match_upc(session, obj_classes):
#     invs = [ {'upc':'48743213',  'supplier_id':1, 'qty':10},
#                {'upc':'9348886',  'supplier_id':1, 'qty':10}]
#     res = match_variation_sku_by_upc(obj_classes.get('variation'), session, invs)
#     assert res is not None


def test_update_inv(session, obj_classes, shop_conn):
    inv =  {'sku':'s2789',  'supplier_id':_supplie_id, 'qty':82}
    update_inventory_db_by_sku(obj_classes, session, inv['sku'], inv)

    res = get_inventory_by_sku(obj_classes, session, 
                            inv['sku'], by_supplier=False)
    
def test_update_front_shop_bulk(obj_classes, session, shop_conn):
    update_instock_front_shop(obj_classes, session, shop_conn, set_inventory_management=True)


def test_update_front_shop(obj_classes, session, shop_conn):
    update_instock_front_shop_by_sku(obj_classes, session, shop_conn, 's2789')
    update_instock_front_shop_by_sku(obj_classes, session, shop_conn, 's22456')