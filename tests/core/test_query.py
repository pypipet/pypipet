from pypipet.core.sql.query import get_variation_instock,get_latest_inventory_update
import pytest
from pprint import pprint


def test_get_variation_instock(session,  obj_classes):
    res = get_variation_instock(obj_classes, session, '0', batch_size=20,
                               params={}, latest_hours=1)

    print(len(res))
    print([(r['sku'], r['qty']) for r in res])

    res = get_variation_instock(obj_classes, session, '0', batch_size=20,
                               params={}, latest_hours=None)

    print(len(res))
    print([(r['sku'], r['qty']) for r in res])

def test_get_latest_inventory_update(session,  obj_classes):
    res = get_latest_inventory_update(obj_classes.get('inventory'), session, '0', 
                     batch_size=10, params={}, latest_hours=1)
    print(len(res))
    print(res)
    
    res = get_latest_inventory_update(obj_classes.get('inventory'), session, '0', 
                     batch_size=10, params={}, latest_hours=None)
    print(len(res))
    print(res)



