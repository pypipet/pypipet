import click 
from .cli import cli
from pypipet.core.operations.utility import get_front_shop_id
from pypipet.core.operations.inventory import update_inventory_bulk
from pypipet.core.operations.inventory import update_instock_qty_db
from pypipet.core.operations.inventory import update_instock_front_shop
# from pypipet.core.operations.inventory import update_instock_qty_db_simple
from pypipet.core.operations.inventory import get_inventory_by_sku
from pypipet.core.operations.inventory import update_instock_front_shop_by_sku
from pypipet.core.fileIO.file_loader import read_csv_file
from .utility import col2dict_update
from pprint import pprint


#do do: add new inventory, view inentory

@cli.command()
@click.argument("action", type=click.Choice(['show', 'edit']))
@click.option("--shop", 
                help="frontshop name (in setting.shops)")
@click.option("--sku",
                help="if multiple sku provided, seperate with comma")
@click.option("--qty", type=int, 
                help="total qty by sku")
@click.option("-f", "--filename",
                help="update inventory with file")
@click.option("--batch", default=100,
                help="batch size to update inventory in database")
@click.option('--skip-shop', is_flag=True, 
                  help="skip updating front shop for action edit.")
@click.option('--ignore-new', is_flag=True, 
                  help="ignore new skus")
@click.pass_context
def inventory(ctx, action, shop, filename, batch, 
                sku,qty, skip_shop, ignore_new):
    """
    add/edit inventory (by skus or by file)
    """
    click.echo(' inventory at... {}'.format(shop))

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
    
    if action == 'edit':
        click.echo('updating inventory, it may take a while \
        (depends on the feed size)')
        _edit_inventory(session, table_classes, shop_conn, filename, 
                        batch,sku,qty, skip_shop, ignore_new)
    elif action == 'show':
        if sku is None:
            click.secho('missing sku',
                fg='yellow')
        sku = sku.split(',')
        for s in sku:
            inv = get_inventory_by_sku(table_classes, session, s, 
                                            by_supplier=True)
            click.echo(f"sku {s} in_stock_qty: {inv}")
    
    session.close()


def _edit_inventory(session, table_classes, shop_conn, filename, 
              batch, sku,qty, skip_shop, ignore_new):
    if filename is not None:
        invs = _get_data_from_file(filename) 
        update_inventory_bulk(table_classes, 
                             session, invs, ignore_new=ignore_new)
        
        #if not skip, update shop
        if not skip_shop:
            update_instock_front_shop(table_classes, session, shop_conn,
                                batch_size=batch,latest_hours=1)
    else:
        click.secho('missing filename', fg='yellow')



def _get_data_from_file(filename):
    data = read_csv_file(filename)
    invs = []
    #validation
    for i, row in data.iterrows():
        if row['sku'].strip() == '':
            click.secho('missing sku in row {}, stop processing'\
                                 .format(i+2), 
                        fg='yellow')
            return 
    
    for i, row in data.iterrows():
        inv = {}
        for k, val in dict(row).items():
            if val.strip() == '':
                continue 
            if k in ['qty', 'supplier_id']: 
                val = int(val)
            if 'cost' in k or 'price' in k: 
                val = float(val) 
            inv[k] = val
        # pprint(inv)
        invs.append(inv)

    return invs