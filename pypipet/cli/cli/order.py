import click 
from .cli import cli
from pypipet.core.operations.utility import get_front_shop_id
from pypipet.core.operations.order import get_orders_from_shop
from pypipet.core.operations.order import  get_order_from_shop_by_id
from pypipet.core.operations.order import  add_order_to_db
from pypipet.core.operations.order import  add_orders_to_db_bulk
from pypipet.core.operations.order import  update_order_to_db
from pypipet.core.operations.order import  get_order_info
from pypipet.core.sql.query_interface import search_exist
from pypipet.core.model.order import Order

from pypipet.core.fileIO.file_loader import read_csv_file
from .utility import col2dict_update
from pprint import pprint

_PROCESSING = 'processing'

@cli.command()
@click.argument("action", type=click.Choice(['sync', 'status', 'show',
                                           'add', 'edit']))
@click.option("--shop", 
                help="frontshop name (in setting.shops)")
@click.option("--order-id",
                help="order id at frontshop")
@click.option("--manual",type=click.Choice(['refunded', 'completed', 
         'processing', 'shipped', 'ready-to-ship',
         'cancelled']), help="manual input for status")
@click.option("-f", "--filename",
                help=" edit order attributes")
@click.pass_context
def order(ctx, action, shop, order_id, manual, filename):
    """
    add/edit orders (by skus or by file)
    """
    click.echo('{} orders at {}...'.format(action, shop))

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

    if action == 'sync':
        if order_id is not None:
            _sync(session, table_classes, shop_conn, order_id=order_id)
        else:
            _sync(session, table_classes, shop_conn)

    elif action == 'status':
        _status(session, table_classes, shop_conn, 
               manual, order_id=order_id)
    elif action == 'show':
        if order_id is None:
            click.echo('missing order_id')
            return 
        _get_order(session, table_classes,shop_conn, order_id)
    elif action == 'add':
        pass 
    elif action == 'edit':
        pass
    else:
        click.secho('action not supported: {}'.format(action),
                fg='yellow')
    
    session.close()


def _get_order(session, table_classes, shop_conn, order_id):
    order_info = get_order_info(table_classes, 
                                session, 
                                params={'destination_order_id': order_id, 
                                'front_shop_id': shop_conn.front_shop_id})
    click.echo(order_info)
    return order_info

def _sync(session, table_classes, shop_conn, order_id=None):
    if order_id is None:
        orders = get_orders_from_shop(table_classes, session, shop_conn)
        add_orders_to_db_bulk(table_classes, session, orders, 
                              shop_conn.front_shop_id)
        click.echo('sync orders total {}'.format(len(orders)))
    else:
        order = Order()
        order.set_order(table_classes, 
                       get_order_from_shop_by_id(order_id, shop_conn))
        add_order_to_db(table_classes, session, order,
                                shop_conn.front_shop_id)
        click.echo('sync order {}'.format(order_id))    

def _status(session, table_classes, shop_conn, manual, order_id=None):
    if order_id is None:
        #update status from frontshop to db
        orders = search_exist(table_classes.get('shop_order'),
                              session,
                              {'status': _PROCESSING})
        update_n = 0
        for order in orders:
            click.echo('updating order {}'.format(order.destination_order_id))
            order_info = shop_conn.get_order_at_shop(
                            destination_order_id=order.destination_order_id)
            if order_info['status'] != _PROCESSING:
                update_order_to_db(table_classes.get('shop_order'),
                            session,
                            {'destination_order_id': order_id,
                            'front_shop_id': shop_conn.front_shop_id,
                            'status': order_info['status']})
                update_n += 1

        click.echo('sync orders total {} out of  {}'.format(update_n, len(orders)))
    else:
        status = None
        if manual is None:
            #udpate order(with order #) status from frontshop to db
            order_info = shop_conn.get_order_at_shop(
                            destination_order_id=order_id)
            status = order_info['status']
        else:
            shop_conn.update_order_status_at_shop(
                destination_order_id = order_id,
                status = manual
            )
            status = manual

        update_order_to_db(table_classes.get('shop_order'),
                            session,
                            {'destination_order_id': order_id,
                            'front_shop_id': shop_conn.front_shop_id,
                            'status': status})

        click.echo('update order {} status to {}'\
                  .format(order_id, status ))    
