import click 
from .cli import cli
from pypipet.core.operations.utility import get_front_shop_id
from pypipet.core.operations.fulfillment import get_shipping_info
from pypipet.core.operations.fulfillment import add_fulfillment_bulk
from pypipet.core.operations.fulfillment import add_fulfillment
from pypipet.core.operations.fulfillment import update_tracking
from pypipet.core.operations.fulfillment import update_fulfillment_to_front_shop
from pypipet.core.sql.query_interface import search_exist
from pypipet.core.fileIO.file_loader import read_csv_file
from .utility import col2dict_update
from pprint import pprint


@cli.command()
@click.argument("action", type=click.Choice(['add', 'edit', 'show']))
@click.option("--shop", 
                help="frontshop name (in setting.shops)")
@click.option("--tracking",
                help="tracking code")
@click.option("--provider",type=click.Choice(['canada_post','usps',
             'ups', 'fedex', 'dhl']), help="shipping service provider")
@click.option("--order-id", help="fronshop order id")
@click.option("-f", "--filename",
                help=" edit tracking info in bulk")
@click.option('--message', is_flag=True, 
                        help="skip updating front shop for action edit.")
@click.pass_context
def fulfillment(ctx, action, shop, tracking, provider, order_id, filename, message):
    """
    add/edit shipping tracking (by skus or by file)
    """
    click.echo('{} fulfillment at {}... send mesage \
     to customer: {}'.format(action, shop, message))

    project = ctx.obj['project']
    config = ctx.obj["config"]
    if config is None:
        click.secho('create project first',
                   fg='yellow')
        return

    project.initialize_project(config)
    table_classes = project.get_table_objects()
    sessionmaker = project.get_session_maker()
    session = sessionmaker()
    
    shop_conn = project.get_shop_connector(shop)
    if shop_conn is None:
        click.secho('shop setting not found: {}'.format(shop),
                   fg='yellow')
        session.close()
        return 
    
    get_front_shop_id(table_classes, session, shop_conn)


    if action == 'add':
        _add_tracking(session, table_classes, shop_conn, order_id, 
                                    tracking, provider, filename, message=message)
    elif action == 'edit':
        _update_fulfillment(session, table_classes, shop_conn, order_id, 
                                          tracking, provider, filename,  message=message)
    elif action == 'show':
        shipment = None
        if tracking is not None:
            shipment = get_shipping_info(table_classes, session,
                                     {'tracking_id': tracking})
        else:
            shipment = get_shipping_info(table_classes, session,
                                     {'destination_order_id': order_id,
                                      'front_shop_id': shop_conn.front_shop_id})
        click.echo(shipment)
    else:
        click.secho('action not supported: {}'.format(action),
                fg='yellow')
    
    session.close()


def _add_tracking(session, table_classes, shop_conn, order_id, 
                         tracking, provider, filename, message=False):
    if filename is None:
        if order_id is None or tracking is None or provider is None:
            click.echo('invalid tracking info')
            return 
        
        data = {
            'tracking_id': tracking,
            'provider': provider,
            'destination_order_id': order_id
        }
        _edit_fulfilment(session, table_classes, data, 
                           shop_conn.front_shop_id,order_id, action=1, 
                           shop_conn=shop_conn, message=message)
        
    else:
        _add_tracking_by_file(session, table_classes, shop_conn, filename, message=message) 

def _add_tracking_by_file(session, table_classes, shop_conn, filename, message=False):
    data = _get_data_from_file(filename)
    for d in data:
        if d.get('front_shop_id') is None or  d['front_shop_id'] == '':
            d['front_shop_id'] = shop_conn.front_shop_id

        _edit_fulfilment(session, table_classes, {
                'tracking_id': d['tracking_id'],
                'provider': d['provider'],
                'destination_order_id': d['destination_order_id']
            }, d['front_shop_id'],d['destination_order_id'], action=1,
            shop_conn=shop_conn, message=message)


def _update_fulfillment(session, table_classes, shop_conn, order_id, 
                            tracking, provider, filename, message=False):
    if filename is None:
        if order_id is None or (tracking is None and provider is None):
            click.echo('invalid tracking info')
            return 
        
        data = {
            'tracking_id': tracking,
            'provider': provider,
            'destination_order_id': order_id
        }
        _edit_fulfilment(session, table_classes, data, 
                shop_conn.front_shop_id,order_id, action=0, 
                shop_conn=shop_conn, message=message)
    else:
        _update_tracking_by_file(session, table_classes, shop_conn, 
                         filename, message=message) 


def _update_tracking_by_file(session, table_classes, shop_conn, filename,
                                                   message=False):
    data = _get_data_from_file(filename)
    for d in data:
        if d.get('front_shop_id') is None or  d['front_shop_id'] == '':
            d['front_shop_id'] = shop_conn.front_shop_id
        
        _edit_fulfilment(session, table_classes, {
                'tracking_id': d['tracking_id'],
                'provider': d['provider'],
            }, d['front_shop_id'],d['destination_order_id'], action=0,
            shop_conn=shop_conn, message=message)

def _edit_fulfilment(session, table_classes, fulfillment_info, 
                 front_shop_id,order_id, action=0, shop_conn=None,message=False):
    """action 0: update
       actiion 1: add"""

    if action == 1:
        fulfillment_info.update({
            'front_shop_id': front_shop_id
            })
        click.echo('adding tracking {}'.format(fulfillment_info))
        add_fulfillment(table_classes, session, fulfillment_info)

    elif action == 0:
        click.echo('update tracking {}'.format(fulfillment_info))
        order_info = _get_order(session, table_classes.get('shop_order'), 
                                order_id, front_shop_id)
        update_tracking(table_classes, session, fulfillment_info,
                                 {'shop_order_id':order_info['id']})
    
    if message:
        # print(fulfillment_info)
        update_fulfillment_to_front_shop(table_classes, session, 
            shop_conn, {}, tracking_info=fulfillment_info)

    return fulfillment_info

def _get_order(session, table_obj, order_id, front_shop_id):
    order = search_exist(table_obj, session, {
        'destination_order_id': order_id,
        'front_shop_id': front_shop_id
    })
    if len(order) > 0:
        return _object2dict(order[0])


def _get_data_from_file(filename):
    data = read_csv_file(filename)
    ff = []

    #validation
    for i, row in data.iterrows():
        if row['destination_order_id'].strip() == '':
            click.secho('row {} missing order id from destination shop'\
                  .format(i+1), 
                        fg='yellow')
            continue 
        if row['tracking_id'].strip() == '':
            click.secho('row {} missing tracking_id from destination shop'\
                  .format(i+1), 
                        fg='yellow')
            continue 
        ff.append(dict(row))

    return ff
    

def _object2dict(table_obj):
    d = {}
    for k in table_obj.__table__.columns.keys():
        d[k] = table_obj.__dict__.get(k, None)
    return d