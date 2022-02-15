from pypipet.core.sql.query_interface import search_exist, update_data
from pypipet.core.sql.query_interface import get_fulfilled_orders
from pypipet.core.sql.query_interface import add_json_to_db
import logging
from .utility import _object2dict
# from datetime import datetime, timedelta

logger = logging.getLogger('__default__')
logger.setLevel(logging.DEBUG)


def get_shipping_info(table_objs, session, params:dict):
    shipment = {}
    ff_params = {}
    if (params.get('destination_order_id') is None\
        or params.get('front_shop_id') is None) \
        and params.get('shop_order_id') is None:

        if params.get('tracking_id') is None:
            logger.debug('invalid params')
            return

        ff_params = {'tracking_id': params['tracking_id']}
    elif params.get('shop_order_id') is not None:
        ff_params = {'shop_order_id': params['shop_order_id']}

    if len(ff_params) > 0:
        ff = get_fulfillment(table_objs.get('fulfillment'), session, ff_params)
        shipment.update(ff)
        if shipment.get('status') is not None:
            shipment['shipping_status'] = shipment['status'] 
            params['shop_order_id'] = shipment['shop_order_id']
    
    if params.get('shop_order_id') is not None:
        params = {'id': params['shop_order_id']}

    order = search_exist(table_objs.get('shop_order'), 
                session, 
                params)
    
    if len(order) == 0:
        logger.debug('order not exist')
        return None 

    if len(ff_params) == 0:
        ff =  get_fulfillment(table_objs.get('fulfillment'), session, 
                             {'shop_order_id': order[0].id})
        shipment.update(ff)
        if shipment.get('status') is not None:
            shipment['shipping_status'] = shipment['status'] 
    
    shipment.update(_object2dict(order[0]))

    #shipping address 
    customer = search_exist(table_objs.get('customer'), 
                   session, 
                   {'id': shipment['shipping_customer_id']})
    if len(customer) > 0:
        customer = _object2dict(customer[0])
        del customer['id']
        shipment.update(customer)

    return shipment


def get_unfulfilled_order_inprocesss(table_objs, session, status='processing', 
                                                               params:dict=None):
    if params is None: params = {}
    params.update({'status': status})
    in_process = search_exist(table_objs.get('shop_order'), session,params )
    if len(in_process) > 0:
        in_process_orders = [_object2dict(r) for r in in_process]
        shop_order_id_list = [r['id'] for r in in_process_orders]
        fulfilled = get_fulfilled_orders(table_objs, session, status=status,
                shop_order_id_list=shop_order_id_list)
        
        fulfilled_order_ids =set( [r['shop_order_id'] for r in fulfilled])
       
        unfilled_orders = []
        for order in in_process_orders:
            if not order['id'] in fulfilled_order_ids:
                unfilled_orders.append(order)

        return unfilled_orders
    logger.debug(f'invalid params {params}')

def get_fulfilled_orders_inprocess(table_objs, session, status='processing', 
                                                              params:dict=None):
    if params is None: params = {}
    params.update({'status': status})
    fulfilled = get_fulfilled_orders(table_objs, session, status=status,
                params=params)
        

    return fulfilled


def add_fulfillment_bulk(table_objs, session, data_list:list):
    for data in data_list:
        add_fulfillment(table_objs, session, data)

def add_fulfillment(table_objs, session, data:dict, **kwargs):
    if data.get('tracking_id') is  None \
        or data.get('provider') is  None :
        logger.debug('invalid fulfiment info')
        return 
    if (data.get('destination_order_id') is None\
        or data.get('front_shop_id') is None) \
        and data.get('shop_order_id') is None:
        logger.debug('invalid identifier info')
        return     
    if data.get('shop_order_id') is None:
        order = _get_order(table_objs.get('shop_order'), 
        session, 
        {
            'destination_order_id': data['destination_order_id'],
            'front_shop_id': data['front_shop_id']
        })
        if order:
            data['shop_order_id'] = order.id
            del data['front_shop_id']

    if data.get('status') is None: data['status'] = 'shipped'

    existing_ff = search_exist(table_objs.get('fulfillment'),session, 
                               {'shop_order_id': data['shop_order_id']})
    
    if existing_ff and len(existing_ff) > 0:
        if kwargs.get('update_exist') == True:
            logger.debug('updating existing tracking')
            return update_data(table_objs.get('fulfillment'), session, 
                            data, {'shop_order_id': data['shop_order_id']})
        else:
            logger.debug(f"existing tracking info . update_exist flag\
                {kwargs.get('update_exist', False)}")
    else:
        return add_json_to_db(table_objs.get('fulfillment'), session, data)

def update_tracking(table_objs, session, data:dict, params: dict):
    if (params.get('destination_order_id') is None\
        or params.get('front_shop_id') is None) \
        and params.get('shop_order_id') is None:
        logger.debug('invalid identifier info')
        return 
    
    if params.get('shop_order_id') is None:
        order = _get_order(table_objs.get('shop_order'), 
        session, 
        {
            'destination_order_id': params['destination_order_id'],
            'front_shop_id': params['front_shop_id']
        })
        if order:
            params['shop_order_id'] = order.id
            del params['front_shop_id']

    if data.get('status') is None: data['status'] = 'shipped'
    update_data(table_objs.get('fulfillment'), session, data, params)

def get_fulfillment(table_obj, session, params):
    ff = search_exist(table_obj,session, params)
    if len(ff) > 0:
        return  _object2dict(ff[0])
    
    # logger.debug('existing fulfillment not found')
    return {}


def update_fulfillment_to_front_shop(table_objs, session, 
             shop_connector, params: dict, tracking_info:dict=None, **kwargs):
    if tracking_info is None or len(tracking_info) == 0:
        if (params.get('destination_order_id') is None \
        or params.get('front_shop_id') is None) and params.get('shop_order_id') is None:
            logger.debug('invalid identifier info')
            return

        if params.get('shop_order_id'):
            params['id'] = params['shop_order_id']
            del params['shop_order_id']

        order = _get_order(table_objs.get('shop_order'),session, params)
        if order:
            tracking_info = get_fulfillment(table_objs.get('fulfillment'), 
                                session,
                                {'shop_order_id': order.id})
        else:
            return
        
    res = shop_connector.add_tracking(
                tracking_info['destination_order_id'],
                tracking_info,
                **kwargs)
    return res



def _get_order(table_obj, session, params):
    order = search_exist(table_obj, 
                session, 
                params)
    
    if order is None or len(order) == 0:
        logger.debug('order not exist')
        return None 
    
    return order[0]