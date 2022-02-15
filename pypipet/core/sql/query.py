from sqlalchemy.sql import func
from sqlalchemy.exc import  SQLAlchemyError, IntegrityError
from sqlalchemy import select, update, desc
from sqlalchemy import and_, or_
from sqlalchemy.sql import text
from sqlalchemy.dialects.postgresql import insert as psql_insert
from pypipet.core.model.utility import get_unique_attrs
import json
from datetime import datetime, timedelta

import logging
logger = logging.getLogger('__default__')

#to do: pytest on this file

def object2dict(obj):
    d = {}
    for k in obj.__table__.columns.keys():
        d[k] = obj.__dict__.get(k, None)
    return d

def exception_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except  SQLAlchemyError as sqlError:
            kwargs.get('logger', logger).debug(sqlError)
    return wrapper

@exception_handler
def query_server_timestamp(session):
    statement = select(func.current_timestamp())
    results = session.execute(statement).first()
    return results

@exception_handler
def query_table_count(table_obj, session):
    count = session.query(table_obj).count()
    return count

def db_insert(obj, table_obj, session):
    """table_obj: sqlalchemy.ext.automap
       session: sqlalchemy session from session maker"""
    table_obj.created_at = func.now()
    table_obj.updated_at = func.now()

    try:
        rd = table_obj(**obj.get_all_attrs())
        session.add(rd)
        session.commit()
        session.refresh(rd)
        return rd
    except TypeError as e:
        logger.debug(e)
        session.rollback()
        logger.debug(json.dumps(obj.get_all_attrs()))
    except IntegrityError as e:
        # constraint on unique value
        logger.debug(f"integraty error {e}")
        session.rollback()
    except  SQLAlchemyError as sqlError:
        logger.debug(sqlError)
        session.rollback()
        logger.debug(json.dumps(obj.get_all_attrs()))

@exception_handler
def db_insert_raw(table_obj, session, data: dict):
    """table_obj: sqlalchemy.ext.automap
       session: sqlalchemy session from session maker"""
    data['created_at'] = func.now()
    data['updated_at']= func.now()
    try:
        rd = table_obj(**data)
        session.add(rd)
        session.commit()
        session.refresh(rd)
        return rd
    except TypeError as e:
        logger.debug(e)
        session.rollback()
        logger.debug(data)
    except IntegrityError as e:
        # constraint on unique value
        logger.debug(f"integraty error {e}")
        session.rollback()
    except  SQLAlchemyError as sqlError:
        logger.debug(sqlError)
        session.rollback()
        logger.debug(data)

@exception_handler
def db_insert_bulk(objs, table_obj, session):
    insert_list = []
    for obj in objs:
        obj.set_attr('created_at', str(func.now()))
        obj.set_attr('updated_at', str(func.now()))
        insert_list.append(obj.get_all_attrs())

    # logger.debug(f"bulk inserting {len(insert_list)}")
    session.bulk_insert_mappings(table_obj, insert_list)
    session.commit()

@exception_handler
def db_insert_raw_bulk(dict_list, table_obj, session):
    for i, _ in enumerate(dict_list):
        dict_list[i]['created_at'] = str(func.now())
        dict_list[i]['updated_at'] = str(func.now())

    # logger.debug(f"bulk inserting {len(dict_list)}")
    session.bulk_insert_mappings(table_obj, dict_list)
    session.commit()

@exception_handler
def db_select(table_obj, session, filters: dict = None):
    if filters is None: filters={}
    statement = select(table_obj).filter_by(**filters)
    results = session.execute(statement).scalars().all()
    return results


@exception_handler
def table_latest_record(table_obj, session, key:str, filters: dict=None):
    if filters is None: filters={}
    statement = select(table_obj)\
        .filter_by(**filters)\
        .order_by(desc(table_obj.__table__.c[key]))
    latest = session.execute(statement).scalars().first()
    return latest


@exception_handler
def db_update(table_obj, session, update_data, filters: dict = None):
    if filters is None: filters={}
    update_data['updated_at'] = str(func.now())
    statement = update(table_obj).\
                    filter_by(**filters).\
                    values(**update_data)
    # print(statement)
    session.execute(statement)
    session.commit()
    return update_data



def db_update_bulk(table_obj, session, data:list):
    dt = str(func.now())
    for d in data:
        d['updated_at'] = dt
    try:
        res = session.bulk_update_mappings(table_obj, data)
        session.commit()
        return res
    except IntegrityError as e:
        # constraint on unique value
        logger.debug(f"bulk update integraty error {e}")
        session.rollback()
    except  SQLAlchemyError as sqlError:
        logger.debug(sqlError)
        session.rollback()
        logger.debug(table_obj)

@exception_handler
def db_raw_query(query, session, params: dict=None):
    if params is None: params={}
    sql = text(query)
    # logger.debug(sql)
    results = session.execute(sql, params)
    data = []
    for r in results.fetchall():
        data.append(dict(r))
    return data


@exception_handler
def db_sum_query(table_obj, session, target, group_by:list, params:dict=None):
    if params is None: params={}
    statement = select(func.sum(target), 
                            *group_by)\
                .filter_by(**params)\
                .group_by(*group_by)
    res = session.execute(statement).all()
    return res

def get_products(table_objs, session, params:dict=None, details=0):
    product = table_objs.get('product')
    if params is None: params={}
    statement = select(table_objs.get('variation')).filter_by(**params)
    variation = statement.subquery()

    if details == 0:
        statement = select(product.product_name, variation.c.sku,
                                variation.c.in_stock, variation.c.upc)\
                    .join_from(product, variation, 
                                variation.c.product_id==product.id)
    elif details == 1:
        statement = select(product.product_name, product.short_description, 
                     product.brand, product.category_id, variation)\
                    .join_from(product, variation, 
                                variation.c.product_id==product.id)
    res = session.execute(statement).all()

    return res

@exception_handler
def filter_order(table_objs, session, params,  start_id=None, start_dt=None):
    shop_order = table_objs.get('shop_order')
    customer = table_objs.get('customer')
    statement = None
    if start_id is not None:
        statement = select(shop_order)\
                .filter(shop_order > start_id)\
                .filter_by(**params)
    elif start_dt is not None:
        statement = select(shop_order)\
                .filter(shop_order.created_at > start_dt)\
                .filter_by(**params)
    else:
        statement = select(shop_order)\
                .filter_by(**params)

    shop_orders = statement.subquery()

    statement = select(shop_orders.c.id, shop_orders.c.destination_order_id, 
                       shop_orders.c.front_shop_id, shop_orders.c.status, 
                       shop_orders.c.order_total, shop_orders.c.order_at,shop_orders.c.currency,
                       customer.first_name, customer.last_name, customer.email)\
                    .join_from(shop_orders, customer, 
                                shop_orders.c.billing_customer_id==customer.id)
    res = session.execute(statement).all()
    return res
                    

@exception_handler
def get_latest_inventory_update(table_obj, session, start_sku, 
                     batch_size=10, params: dict = None, latest_hours=24):
    if params is None: params={}
    if latest_hours is None:
        return get_latest_inventory_update_all(table_obj, session, start_sku, 
                     batch_size, params)
    dt = query_server_timestamp(session)
    updated_after = dt[0]-timedelta(hours=latest_hours)
    statement = None 
    if start_sku is not None:
        statement = select(table_obj.sku)\
                    .distinct()\
                    .filter(table_obj.sku > start_sku)\
                    .filter_by(**params)\
                    .filter(or_(table_obj.updated_at > updated_after, 
                                    table_obj.created_at>updated_after))\
                    .order_by(table_obj.sku)\
                    .limit(batch_size)
    else:
        statement = select(table_obj.sku)\
                    .distinct()\
                    .filter_by(**params)\
                    .filter(or_(table_obj.updated_at > updated_after, 
                                    table_obj.created_at>updated_after))\
                    .order_by(table_obj.sku)\
                    .limit(batch_size)


    res = session.execute(statement).all()
    if len(res) == 0:
        return []

    filtered_sku = [r.sku for r in res]

    statement = select(func.sum(table_obj.qty).label('in_stock'), table_obj.sku)\
                    .filter(or_(table_obj.updated_at > updated_after, 
                                            table_obj.created_at>updated_after))\
                    .filter(table_obj.sku.in_(filtered_sku))\
                    .group_by(table_obj.sku)
    
    
    
    res = session.execute(statement).all()

    return res

@exception_handler
def get_latest_inventory_update_all(table_obj, session, start_sku, 
                     batch_size=10, params: dict = None):
    if params is None: params={}
    statement = None 
    if start_sku is not None:
        statement = select(table_obj.sku)\
                    .distinct()\
                    .filter(table_obj.sku > start_sku)\
                    .filter_by(**params)\
                    .order_by(table_obj.sku)\
                    .limit(batch_size)
    else:
        statement = select(table_obj.sku)\
                    .distinct()\
                    .filter_by(**params)\
                    .order_by(table_obj.sku)\
                    .limit(batch_size)


    res = session.execute(statement).all()
    if len(res) == 0:
        return []

    filtered_sku = [r.sku for r in res]

    statement = select(func.sum(table_obj.qty).label('in_stock'), table_obj.sku)\
                    .filter(table_obj.sku.in_(filtered_sku))\
                    .group_by(table_obj.sku)
    
    
    
    res = session.execute(statement).all()

    return res

@exception_handler
def get_variation_instock(table_objs, session, start_product_id, batch_size=20,
                               params: dict=None, latest_hours=24):
    if params is None: params={}
    if latest_hours is None:
        #get dt from earliest datetime
        return get_variation_instock_all(table_objs, session, start_product_id, 
                                     batch_size, params)

    
    dt = query_server_timestamp(session)
    updated_after = dt[0]-timedelta(hours=latest_hours)
    
    params.update({
        'available': True,
        'is_current_price': True
    })

    variation = table_objs.get('variation')
    destination = table_objs.get('destination')
    
    statement = None
    if start_product_id is None:
        statement = select(variation.in_stock.label("qty"), 
                            variation.sku.label("sku"), 
                            destination.destination_product_id.label("product_id"),
                            destination.destination_parent_id.label("parent_id"),
                            destination.inventory_item_id.label("inventory_item_id"))\
                .join_from(variation, destination, 
                            variation.sku==destination.sku)\
                .filter_by(**params) \
                .filter(variation.updated_at > updated_after)\
                .filter(variation.in_stock >=0)\
                .filter(destination.destination_product_id != None)\
                .order_by(destination.destination_product_id)\
                .limit(batch_size)
    else:
        statement = select(variation.in_stock.label("qty"), 
                            variation.sku.label("sku"), 
                            destination.destination_product_id.label("product_id"),
                            destination.destination_parent_id.label("parent_id"),
                            destination.inventory_item_id.label("inventory_item_id"))\
                .join_from(variation, destination, 
                            variation.sku==destination.sku)\
                .filter_by(**params) \
                .filter(variation.updated_at > updated_after)\
                .filter(destination.destination_product_id > start_product_id)\
                .filter(variation.in_stock >=0)\
                .filter(destination.destination_product_id != None)\
                .order_by(destination.destination_product_id)\
                .limit(batch_size)
    # print(statement)
    res = session.execute(statement).all()

    return res

@exception_handler
def get_variation_instock_all(table_objs, session, start_product_id, batch_size=20,
                               params: dict=None):
    if params is None: params={}
    params.update({
        'available': True,
        'is_current_price': True
    })

    variation = table_objs.get('variation')
    destination = table_objs.get('destination')
    
    statement = None
    if start_product_id is None:
        statement = select(variation.in_stock.label("qty"), 
                            variation.sku.label("sku"), 
                            destination.destination_product_id.label("product_id"),
                            destination.destination_parent_id.label("parent_id"),
                            destination.inventory_item_id.label("inventory_item_id"))\
                .join_from(variation, destination, 
                            variation.sku==destination.sku)\
                .filter_by(**params) \
                .filter(variation.in_stock >=0)\
                .filter(destination.destination_product_id != None)\
                .order_by(destination.destination_product_id)\
                .limit(batch_size)
    else:
        statement = select(variation.in_stock.label("qty"), 
                            variation.sku.label("sku"), 
                            destination.destination_product_id.label("product_id"),
                            destination.destination_parent_id.label("parent_id"),
                            destination.inventory_item_id.label("inventory_item_id"))\
                .join_from(variation, destination, 
                            variation.sku==destination.sku)\
                .filter_by(**params) \
                .filter(destination.destination_product_id > start_product_id)\
                .filter(variation.in_stock >=0)\
                .filter(destination.destination_product_id != None)\
                .order_by(destination.destination_product_id)\
                .limit(batch_size)
    # print(statement)
    res = session.execute(statement).all()

    return res

@exception_handler
def get_fulfilled_order_in_processing(table_objs, session, status='processing', params:dict=None):
    statement = None
    if params is None: params={}
    if params.get('shop_order_id_list') is not None:
        sql = 'select * from fulfillment where shop_order_id=ANY(:shop_order_id_list)'
        return db_raw_query(sql, session, params={'shop_order_id_list': params['shop_order_id_list']}) 
    else:
        shop_order = table_objs.get('shop_order')
        fulfillment = table_objs.get('fulfillment')
        params.update({'status': status})
        statement = select(shop_order).filter_by(**params)
        orders = statement.subquery()

        statement = select(orders.c.id.label("shop_order_id"), 
                        orders.c.destination_order_id,
                        orders.c.front_shop_id, 
                        fulfillment.id, fulfillment.tracking_id, 
                        fulfillment.provider)\
                    .join_from(orders, fulfillment)
        res = session.execute(statement).all()
        
        return res

@exception_handler
def get_destination_parent(table_obj, session, front_shop_id, skus):
    sql = 'select destination_parent_id from destination where \
    front_shop_id=:front_shop_id and sku=ANY(:skus)'
    res = db_raw_query(sql, session, params={
        'front_shop_id': front_shop_id,
        'skus': skus
    })
    if res and len(res) >0 and res[0].get('destination_parent_id'):
        return res[0]
    

    #if other sku was added as simple product(WC) without parent
    sql = 'select destination_product_id from destination where \
    front_shop_id=:front_shop_id and sku=ANY(:skus) and \
    destination_parent_id is NULL'
    res = db_raw_query(sql, session, params={
        'front_shop_id': front_shop_id,
        'skus': skus
    })
    if res and len(res) >0 and res[0].get('destination_product_id'):
        return res[0]

@exception_handler
def get_instock_by_skus(session, front_shop_id, skus):
    sql = 'select destination_product_id, inventory_item_id, in_stock \
    from variation join destination on variation.sku=destination.sku where \
    front_shop_id=:front_shop_id and available=True and is_current_price=True \
    and variation.sku=ANY(:skus) '
    res = db_raw_query(sql, session, params={
        'front_shop_id': front_shop_id,
        'skus': skus
    })
    if res and len(res) >0:
        return res
