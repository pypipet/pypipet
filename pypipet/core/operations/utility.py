from pypipet.core.sql.query_interface import search_exist


def get_front_shop_id(table_objs, session, shop_connector):
    front_shop = search_exist(
                            table_objs.get('front_shop'), 
                            session, 
                            {'name': shop_connector.shop_name})
    
    if front_shop is not None and len(front_shop):
        shop_connector.set_front_shop_id(front_shop[0].id)


def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def _object2dict(table_obj):
    d = {}
    for k in table_obj.__table__.columns.keys():
        d[k] = table_obj.__dict__.get(k, None)
    return d  