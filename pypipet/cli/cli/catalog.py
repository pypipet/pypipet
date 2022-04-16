import click 
from .cli import cli
from pypipet.core.operations.utility import get_front_shop_id
from pypipet.core.operations.frontshop import add_taxonomy_to_db
from pypipet.core.operations.frontshop import add_product_to_db_bulk
from pypipet.core.operations.frontshop import add_product_to_db
from pypipet.core.operations.frontshop import add_destination_to_db
from pypipet.core.operations.frontshop import load_products_from_shop
from pypipet.core.fileIO.file_loader import read_csv_file
from .utility import col2dict
from pprint import pprint

@cli.command()
@click.argument("source_type", type=click.Choice(["shop", "file"]))
@click.option("--shop", 
                help="frontshop name (in setting.shops)")
@click.option("-f", "--filename", default='',
                help="product feed csv")
@click.option("--currency", default='USD') 
@click.pass_context
def catalog(ctx,source_type, shop, filename, currency):
    """
    import catalog from frontshop or files
    for file import, (generate template first)
    """
    click.echo('loading products from {}...'.format(source_type))
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
   
    if source_type == 'shop':
        #add taxonomy
        # click.echo('sync categories...')
        # add_taxonomy_to_db(table_classes.get('category'), 
        #                    session, 
        #                    shop_conn)
        #pull products
        _load_from_shop_batch(table_classes, session, 
                         shop_conn, 
                         default_brand=project.config['default_brand'],
                         currency=currency)

    elif source_type == 'file':
        _load_from_file(table_classes, session, filename,
                         shop_conn, 
                         default_brand=project.config['default_brand'],
                         currency=currency) 
    else:
        click.secho('invalid source to load products',
                   fg='yellow')
    session.close()

def _load_from_shop_batch(table_objs, session, 
                         shop_connector, default_brand='',
                         currency='USD'):
    load_products_from_shop(table_objs, session, shop_connector, 
                         start_from=1, currency='USD')
        

def _load_from_file(table_objs, session, filename,
                         shop_connector, default_brand='',
                         currency='USD'):
    data = read_csv_file(filename)
    must_exist_fields = ['product.category', 
                         'product.product_name',
                         'variation.sku']
    
    #validation
    for i, row in data.iterrows():
        sku = str(row['variation.sku'])
        # click.echo('row {}: sku {}'.format(i, sku))
        for key in must_exist_fields:
            if row[key].strip() == '':
                click.secho('missing {} at {}, stop importing'\
                                 .format(key, sku), 
                        fg='yellow')
                return 
    
    products = []
    for i, row in data.iterrows():
        sku = str(row['variation.sku'])
        click.echo('row {}: sku {}'.format(i, sku))
        p = col2dict(sku, row, default_brand)
        products.append(p)
        
    click.echo('editing database')
    add_product_to_db_bulk(table_objs, session, shop_connector, 
                          products, currency=currency)


        