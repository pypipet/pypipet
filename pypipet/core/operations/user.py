from pypipet.core.model.user import User
from .utility import _object2dict
from pypipet.core.sql.query_interface import (
    add_to_db, search_exist, update_data)

import logging
logger = logging.getLogger('__default__')

def register_new_user(table_objs, session, user):
    if user is dict:
        user = User(user)
    
    return add_to_db(table_objs.get(user.__table_name__), session, user) 


def find_users(table_obj, session, params):
    res = search_exist(table_obj, session, params)
    if res and len(res) >0:
        return [_object2dict(r) for r in res]


def change_password():
    pass