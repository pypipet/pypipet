from pypipet.core.sql.query_interface import search_exist, update_data
from pypipet.core.sql.query_interface import add_json_to_db
import logging
from .utility import _object2dict
# from datetime import datetime, timedelta

logger = logging.getLogger('__default__')
logger.setLevel(logging.DEBUG)


def get_static_data(table_obj, session, params:dict=None):
    if params is None: params = {}
    res = search_exist(table_obj, session, params)
    if res:
        return [_object2dict(r) for r in res]


def add_static_data(table_obj, session, data):
    return add_json_to_db(table_obj, session, data)

def edit_static_data(table_objs, session, data, target):
    if data.get('id') is not None:
        update_data(table_objs.get(target),
                    session,
                    data,
                    {'id': data['id']})
    if target == 'supplier' and data.get('name') is not None:
        update_data(table_objs.get(target),
                    session,
                    data,
                    {'name': data['name']}) 
    elif target == 'front_shop' and data.get('name') is not None:
        update_data(table_objs.get(target),
                    session,
                    data,
                    {'name': data['name']})
    elif target == 'tax' and data.get('name') is not None:
        update_data(table_objs.get(target),
                    session,
                    data,
                    {'name': data['name']}) 
    elif target == 'category' and data.get('category') is not None:
        update_data(table_objs.get(target),
                    session,
                    data,
                    {'category': data['category']}) 
    else:
        logger.debug('invalid input')

        