# from pypipet.core.shop_conn.gateway import *
from pypipet.core.model.order import Order
from pypipet.core.sql.query_interface import search_exist, get_order, get_filtered_orders
from pypipet.core.sql.query_interface import add_if_not_exist, db_insert_bulk
from pypipet.core.sql.query_interface import get_destination, update_data
from pypipet.core.sql.query_interface import get_latest_record, add_json_to_db
from .utility import get_front_shop_id, _object2dict

import logging
logger = logging.getLogger('__default__')



def add_orders_to_db_bulk(table_objs, session, orders:list, front_shop_id: int):
    
    for order in orders:
        if type(order) is dict:
            order_obj = Order()
            order_obj.set_order(table_objs, order)
        else:
            order_obj = order
        add_order_to_db(table_objs, session, order_obj,front_shop_id)


    session.close() 

def add_order_to_db(table_objs, session, order:Order, front_shop_id:int):
    #billing customer
    billing_customer = order.billing_customer
    if billing_customer:
        res = add_if_not_exist(table_objs.get(billing_customer.__table_name__), 
                        session, 
                        billing_customer,
                        unique_keys= ['email'])
        order.set_attr('billing_customer_id', res.id)

    #shipping customer
    shipping_customer = order.shipping_customer
    if shipping_customer:
        search_keys = ['first_name', 'last_name', 'postcode']
        if shipping_customer.get_attr('email') is not None:
            search_keys.append('email')
        res = add_if_not_exist(table_objs.get(shipping_customer.__table_name__), 
                            session, 
                            shipping_customer,
                            unique_keys=search_keys)
        order.set_attr('shipping_customer_id', res.id)
        # print(res.id)

    order.set_attr('front_shop_id', front_shop_id)

    res = search_exist(table_objs.get(order.__table_name__),
                       session, 
                       {'destination_order_id': order.destination_order_id})
    if len(res) > 0:
        order.update_order_id(res[0].id)
    else:
        res =add_json_to_db(table_objs.get(order.__table_name__), 
                        session, 
                        order.get_all_attrs())
        order.update_order_id(res['id'])
    
    if len(order.order_items) > 0:
        table_obj = table_objs.get(order.order_items[0].__table_name__)
        for item in order.order_items:
            dests = get_destination(
                table_objs.get('destination'),
                session,
                params = {
                    'sku': item.sku,
                    'front_shop_id': front_shop_id
                }
            )
            if dests is None or len(dests) == 0:
                logger.debug(f"order {res['id']} no product found at destination shop. \
                    sku {item.sku}")
                return None
            item.set_attr('destination_id', dests[0]['id'])

            #by default, ship all as request
            if item.get_attr('ship_qty') is None:
                item.set_attr('ship_qty', item.order_qty)

        db_insert_bulk(order.order_items, 
                      table_obj,
                      session)
    
    if order.trackings:
        for tracking in order.trackings:
            res =add_json_to_db(table_objs.get('fulfillment'), 
                        session, 
                        tracking)

    

def get_orders_from_shop(table_objs, session, shop_connector, **kwargs):
    latest_order_id = kwargs.get('latest_order_id')
    if latest_order_id is None:
        previous_upddate = get_latest_record(
                            table_objs.get('shop_order'), 
                            session, 
                            key='destination_order_id',
                            params={'front_shop_id': shop_connector.front_shop_id})
        
        if previous_upddate:
            latest_order_id = previous_upddate.destination_order_id
    
    order_data = shop_connector.sync_shop_orders(
                    latest_order_id = latest_order_id)
    
    # orders = []
    # for item in order_data:
    #         order = Order()
    #         order.set_order(table_objs, item)
    #         orders.append(order)
    return order_data

def get_order_from_shop_by_id(shop_order_id, shop_connector):
    order_info = shop_connector.get_order_at_shop(
                                   destination_order_id=shop_order_id)
    return order_info

def get_order_info(table_objs, session, params, item_info=True):
    order_info = get_order(table_objs, session, 
                        params=params, item_info=item_info)
    return order_info

def get_order_by_status(table_obj, session, status, params:dict=None):
    if params is None: params = {}
    params.update({'status': status})
    orders = search_exist(table_obj,
                          session,
                          params)
    if len(orders) > 0 :
        return [_object2dict(order) for order in orders]
    return orders


def get_orders(table_objs, session, params, **kwargs):
    return get_filtered_orders(table_objs, session, params=params, **kwargs)




def update_order_to_db(table_obj, session, order_info:dict):
    if order_info.get('id') is not None:
        shop_order_id = order_info['id']
        del order_info['id']
        return update_data(table_obj, 
                    session, 
                    order_info, 
                    {'id': shop_order_id})
        order_info['id'] = shop_order_id
    elif order_info.get('destination_order_id') is not None \
    and order_info.get('front_shop_id') is not None:
        return update_data(table_obj, 
                    session, 
                    order_info, 
                    {'destination_order_id': order_info['destination_order_id'],
                     'front_shop_id': order_info['front_shop_id']})
    else:
        logger.debug(f'invalid order identifier {order_info}')





def sync_order_change_from_shop(table_objs, session, shop_connector, destination_order_id):
    order_info = get_order_from_shop_by_id(destination_order_id, shop_connector)

    order = Order()
    order.set_order(table_objs, order_info)
    order.set_attr('front_shop_id', shop_connector.front_shop_id)
    update_order_to_db(table_objs.get('shop_order'), session, order.get_all_attrs())

    #get order.id
    order_id = None
    exist_order = search_exist(table_objs.get('shop_order'), session, 
                    {'destination_order_id': destination_order_id,
                    'front_shop_id': shop_connector.front_shop_id})
    if exist_order and len(exist_order) > 0:
        order_id = exist_order[0].id

    for item in order.order_items:
        update_order_item_to_db(table_objs, session, shop_connector.front_shop_id, 
                        item.get_all_attrs(),  
                        params={'destination_product_id': item.destination_product_id,
                                'shop_order_id': order_id})
    
def update_order_item_to_shop(shop_connector, destination_order_id, order_items:list):
    items = {}
    for item in order_items:
        if item.get('destination_product_id') is None:
            logger.debug(f'missing destination_product_id {item}')
            continue
        items[item['destination_product_id']] = item
    if len(items) == 0:
        return 
    print(items)
    return shop_connector.update_order_item_at_shop(
                            destination_order_id,
                            items)


def update_order_item_to_db(table_objs, session, front_shop_id, 
                                   order_item: dict,  params: dict):
    exist_item = search_exist(table_objs.get('order_item'), session, params)
    if len(exist_item) > 0:
        exist_item = exist_item[0]
        update_data(table_objs.get('order_item'), session, 
                      order_item, {'id': exist_item.id})
    else:
        print('add new order item', order_item)
        dests = get_destination(
            table_objs.get('destination'),
            session,
            params = {
                'destination_product_id': order_item['destination_product_id'],
                'front_shop_id': front_shop_id
            }
        )
        if dests is None or len(dests) == 0:
            logger.debug('no product found at destination shop')
            return None
        order_item['destination_id'] = dests[0]['id']

        #by default, ship all as request
        if order_item.get('ship_qty') is None:
            order_item['ship_qty'] = order_item['order_qty']

        add_json_to_db(table_objs.get('order_item'), session, order_item)



def update_customer_to_db(table_obj, session, customer_info, **kwargs):
    params = {}
    if kwargs.get('id') is not None:
        params['id'] = kwargs['id']
    elif kwargs.get('email') is not None:
        params['email'] = kwargs['email']
    else:
        logger.debug('invalid customer id or email')
        return 

    return update_data(table_obj, 
                session, 
                customer_info, 
                params)

def update_customer_to_shop( session, shop_connector, data, 
                    destination_order_id, is_billing=False,is_shipping=False):
    return shop_connector.update_customer_at_shop(
                                    destination_order_id, 
                                    data, 
                                    is_billing=is_billing,
                                    is_shipping=is_shipping) 

    
  
def send_message_to_customer(shop_connector, destination_order_id, message):
    shop_connector.send_message(destination_order_id, 
                                message)

