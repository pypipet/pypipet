import click 
from .cli import cli
from pypipet.core.operations.utility import get_front_shop_id
from pypipet.core.operations.frontshop import update_product_to_db
from pypipet.core.operations.frontshop import update_variation_to_db
from pypipet.core.operations.frontshop import update_destination_to_db
from pypipet.core.operations.frontshop import update_product_at_front_shop, update_product_at_front_shop_bulk
from pypipet.core.operations.frontshop import add_variation_to_shop, add_product_to_shop
from pypipet.core.operations.frontshop  import get_product_with_variations,get_product_info
from pypipet.core.sql.query_interface import  search_exist
from pypipet.core.operations.inventory import get_inventory_by_sku, update_instock_front_shop
from pypipet.core.fileIO.file_loader import read_csv_file
from .utility import col2dict_update,map_product_sku_for_launch
from pprint import pprint

@cli.command()
@click.argument("action", type=click.Choice(['launch', 'deactivate', 'activate',
                                             'edit', 'show']))
@click.option("--shop", 
                help="frontshop name (in setting.shops)")
@click.option("--sku",
                help="if multiple sku provided, seperate with comma")
@click.option("-f", "--filename",
                help=" edit product attributes")
@click.option("--price",
                help=" price for lauching product to frontshop")
@click.option("--currency", default='USD',
                help=" currency for lauching product to frontshop")
@click.option("--include-stock", is_flag=True,
                help=" update stock for lauching product to frontshop(shopify only)")
@click.option('--skip-shop', is_flag=True, 
                        help="skip updating front shop for action edit.")
@click.pass_context
def product(ctx, action, shop, sku, price, currency, filename, include_stock,skip_shop):
    """
    add/edit products (by sku or file)
    """
    click.echo('{} products at {}. skip-shop {}'.format(
        action, shop, skip_shop))
    if sku is None and filename is None:
        click.echo('product identifier not found')
        return

    if sku is not None:
        sku = sku.split(',')

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

    if action == 'launch':
        #to do, launch by file
        if sku is None and filename is None:
            click.echo('missing feeds')
            return 
        if sku and price is None:
            click.echo('missing price')
            return
        
        if filename is not None:
            click.echo('launch by file {}'.format(filename))
            _launch_to_shop_by_file(session, table_classes, shop_conn, 
                                currency,
                                project.config.get('attr_list'),
                                project.config.get('variation_attrs'),
                                filename) 
        else: 
            price = float(price)
            _launch_to_shop(session, table_classes, shop_conn, 
                                    sku, price, currency,
                                    project.config.get('attr_list'),
                                    project.config.get('variation_attrs'))
        if include_stock:
            click.echo('updating instock qty...')
            _update_stock_for_launching(session, table_classes, shop_conn)
            
    elif action == 'deactivate':
        if sku is None:
            click.echo('missing sku')
            return
        _change_status(session, table_classes, shop_conn, 
                                       sku, False, skip_shop)
    elif action == 'activate':
        if sku is None:
            click.echo('missing sku')
            return
        _change_status(session, table_classes, shop_conn, 
                                       sku, True, skip_shop)
    elif action == 'edit':
        if filename is None:
            click.echo('missing data file')
            return
        prods = _get_data_from_file(filename, action)
        click.echo('total product to edit {}'.format(len(prods)))
        _edit_product(session, table_classes, 
                      shop_conn, prods, skip_shop)
    elif action == 'show':
        if sku is None:
            click.echo('missing sku')
            return
        for s in sku:
            variation_info = get_product_with_variations(
                    table_classes, session, 
                    {'sku': s}, 
                     include_published=True, 
                     front_shop_id=shop_conn.front_shop_id)
            click.echo(variation_info)
    else:
        click.secho('action not supported: {}'.format(action),
                fg='yellow')
    
    session.close()

def _launch_to_shop_by_file(session, table_classes, shop_conn,  
                            currency, attrs, variation_attrs, filename):
    data = _get_data_from_file(filename, 'launch')
    
    for sku_price in data:
        product_info = get_product_info(table_classes, session, shop_conn, 
                    sku=sku_price['sku'],
                    include_category=True)
        res = add_product_to_shop(table_classes, session, shop_conn, product_info, 
                                        price=sku_price['price'],
                                        currency=currency,
                                        attr_list = attrs,
                                        variation_attrs=variation_attrs
                                        )
                             
        click.echo('sku {} add to shop.. success.. {}'.format(sku_price['sku'], res is not None))


def _launch_to_shop(session, table_classes, shop_conn, skus, 
                            price, currency, attrs, variation_attrs):
    for sku in skus:
        product_info = get_product_info(table_classes, session, shop_conn, 
                    sku=sku,
                    include_category=True)
        res = add_product_to_shop(table_classes, session, shop_conn, product_info, 
                                        price=price,
                                        currency=currency,
                                        attr_list = attrs,
                                        variation_attrs=variation_attrs
                                        )
                             
        click.echo('sku {} add to shop.. success.. {}'.format(sku, res is not None))

def _update_stock_for_launching(session, table_classes, shop_conn):
    update_instock_front_shop(table_classes, session, shop_conn)

def _change_status(session, table_classes, shop_conn, 
                        skus, status, skip_shop):
    for sku in skus:
        update_destination_to_db(table_classes.get('destination'),
                                     session,
                                     {'available': status, 'sku': sku},
                                     shop_conn.front_shop_id
                                     )
        
        if skip_shop is False:
            update_data = {'destination': {'available': status}}
            inv = 0
            if status:
                qty = get_inventory_by_sku(table_classes,
                                           session, sku)
                if qty: inv = qty

            update_data['variation'] ={
                'in_stock': inv
            }
            res = update_product_at_front_shop(
                                 table_classes, 
                                 session, 
                                 shop_conn, 
                                 update_data, 
                                 sku) 
            if res is None:
                click.echo('sku {} update error'.format(sku))

def _edit_product(session, table_classes, shop_conn, 
                                       products, skip_shop):
    for p in products:
        click.echo('updating sku {}'.format(p['variation']['sku']))
        if len(p['product']) > 0:
            if p['product'].get('id') is None:
                product_id = _get_product_id_by_sku(table_classes.get('variation'), 
                                                   session, p['variation']['sku'])
                if product_id is None:
                    click.echo('invalid sku, product not found')
                    return
                p['product']['id'] = product_id

            update_product_to_db(table_classes, 
                           session, 
                           p['product'])
        
        if len(p['variation']) > 0:
            update_variation_to_db(table_classes.get('variation'), 
                           session, 
                           p['variation'])
        
        if len(p['destination']) > 0:
            if p['destination'].get('sku') is None:
               click.secho('missing destination sku: {}'.format(p),
                fg='yellow')  
               return 
            update_destination_to_db(table_classes.get('destination'),
                                     session,
                                     p['destination'],
                                     shop_conn.front_shop_id
                                     )
        
    if skip_shop is False:
        click.echo('updating frontshop, total {}'.format(len(products)))
        update_product_at_front_shop_bulk(table_classes, session, 
                                shop_conn, products, batch_size=50)
        

def _get_data_from_file(filename, action):
    data = read_csv_file(filename)
    if action == 'launch':
        return map_product_sku_for_launch(data) 
    else:
        products = []
        #validation
        for i, row in data.iterrows():
            sku = str(row['variation.sku'])
            if sku is None or sku.strip() == '':
                click.secho('missing {}, stop processing'\
                                    .format(sku), 
                            fg='yellow')
                return 

        for i, row in data.iterrows():
            sku = str(row['variation.sku'])
            p = col2dict_update(sku, row)
            # pprint(p)
            products.append(p)

        return products


def _get_product_id_by_sku(table_obj, session, sku):
    vari = search_exist(table_obj, session, {'sku': sku})
    if len(vari) > 0:
        return vari[0].product_id
