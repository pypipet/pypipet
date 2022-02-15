from pypipet.cli import cli
import pytest

_shop_name = 'home_site'
_order_id = '49455'

def exception_handler(func):
    def wrapper(cli_runner, *args, **kwargs):
        res = func(cli_runner,*args, **kwargs)
        if res.exit_code == 0:
            print(res.output)
        else:
            print(res.stdout)
            print(res.__dict__)
            
    return wrapper

@exception_handler
def test_cli(cli_runner):
    return cli_runner.invoke(cli, ['--log-level', 'debug'])

@exception_handler
def test_new(cli_runner):
    return cli_runner.invoke(cli, ['-v', 'new', 'new_proj'])

@exception_handler
def test_init(cli_runner):
    return cli_runner.invoke(cli, ['initialize'])

# @exception_handler
def test_template(cli_runner):
    cli_runner.invoke(cli, ['template','--file', 'product'])
    cli_runner.invoke(cli, ['template','--file', 'product_update'])
    cli_runner.invoke(cli, ['template','--file', 'order'])
    cli_runner.invoke(cli, ['template','--file', 'customer'])
    cli_runner.invoke(cli, ['template','--file', 'inventory'])
    cli_runner.invoke(cli, ['template','--file', 'fulfillment'])
    cli_runner.invoke(cli, ['template','--file', 'supplier'])
    cli_runner.invoke(cli, ['template','--file', 'front_shop'])
    cli_runner.invoke(cli, ['template','--file', 'tax'])
    cli_runner.invoke(cli, ['template','--file', 'category'])

@exception_handler
def test_catalog_help(cli_runner):
    return cli_runner.invoke(cli, ['catalog', '--help'])

@exception_handler
def test_catalog_shop(cli_runner):
    return cli_runner.invoke(cli, ['catalog', 'shop', '--shop', _shop_name])

@exception_handler
def test_catalog_file(cli_runner):
    return cli_runner.invoke(cli, ['catalog', 'file', '--shop', _shop_name,
                              '-f', './product_template.csv'])

@exception_handler
def test_product_view(cli_runner):
    return cli_runner.invoke(cli, ['product', 'show',
                                    '--shop', _shop_name,
                                    '--sku', 's2789'])  #with variations
@exception_handler
def test_product_view2(cli_runner):
    return cli_runner.invoke(cli, ['product', 'activate',
                                    '--shop', _shop_name,
                                    '--sku', 'W39528092'])

@exception_handler
def test_product_edit(cli_runner):
    return cli_runner.invoke(cli, ['product', 'edit',
                                    '--shop', _shop_name,
                                    '-f', 'product_update_template.csv'])
@exception_handler
def test_product_sku(cli_runner):
    return cli_runner.invoke(cli, ['product', 'deactivate',
                                    '--shop', _shop_name,
                                    '--sku', 's2789']) 



@exception_handler
def test_product_launch(cli_runner):
    return cli_runner.invoke(cli, ['product', 'launch',
                                    '--shop', _shop_name,
                                    '--sku', 'k4999',
                                    '--price', '100.99'])

@exception_handler
def test_order_show(cli_runner):
    return cli_runner.invoke(cli, ['order', 'show', '--shop', _shop_name,
                                   '--order-id', _order_id])

@exception_handler
def test_order_sync(cli_runner):
    return cli_runner.invoke(cli, ['order', 'sync', '--shop', _shop_name,
                                   ])

@exception_handler
def test_order_status(cli_runner):
    return cli_runner.invoke(cli, ['order', 'status', '--shop', _shop_name,
                                   '--order-id', _order_id, '--manual', 'processing'])

@exception_handler
def test_shipping_view(cli_runner):
    return cli_runner.invoke(cli, ['fulfillment', 'show', '--shop', _shop_name, 
                                   '--order-id', _order_id, 
                                   ])

@exception_handler
def test_shipping_add(cli_runner):
    return cli_runner.invoke(cli, ['fulfillment', 'add', '--shop', _shop_name, 
                                   '--order-id', _order_id, 
                                   '--provider', 'canada_post',
                                   '--tracking', '111111'])

@exception_handler
def test_shipping_edit(cli_runner):
    return cli_runner.invoke(cli, ['fulfillment', 'edit', '--shop', _shop_name, 
                                   '--order-id', _order_id, 
                                   '--provider', 'canada_post',
                                   '--tracking', '222222'])

@exception_handler
def test_shipping_add_file(cli_runner):
    return cli_runner.invoke(cli, ['fulfillment', 'add', '--shop', _shop_name, 
                                   '-f', 'fulfillment_template.csv' 
                                   ])


@exception_handler
def test_shipping_message(cli_runner):
    return cli_runner.invoke(cli, ['fulfillment', 'add', '--shop', _shop_name, 
                                   '--order-id', _order_id, 
                                   '--provider', 'canada_post',
                                   '--tracking', '111231','--message'],
                                   )

@exception_handler
def test_inventory_edit(cli_runner):
    return cli_runner.invoke(cli, ['inventory', 'edit', '--shop', _shop_name,
                                   '-f', 'inventory_template.csv'])


@exception_handler
def test_inventory_view(cli_runner):
    return cli_runner.invoke(cli, ['inventory', 'show', '--shop', _shop_name,
                                   '--sku', 's22123'])



@exception_handler
def test_static_view(cli_runner):
    return cli_runner.invoke(cli, ['static', 'show', '--target', 'tax'])


@exception_handler
def test_static_add(cli_runner):
    return cli_runner.invoke(cli, ['static', 'add', '--target', 'front_shop', 
                                               '-f', 'front_shop_template.csv'])

@exception_handler
def test_static_edit(cli_runner):
    return cli_runner.invoke(cli, ['static', 'edit', '--target', 'supplier', 
                                               '-f', 'supplier_template.csv'])

# @exception_handler
# def test_api(cli_runner):
#     return cli_runner.invoke(cli, ['api', 'start'])