import click 
from .cli import cli
import pandas as pd

@cli.command()
@click.option("--file", type=click.Choice(['product', 'product_update',
                     'order', 'customer', 'inventory', 'fulfillment',
                    'supplier', 'front_shop', 'tax', 'category' ]))
@click.pass_context
def template(ctx,file):
    """
    generate csv template for importing
    """
    click.echo('generate template: {}'.format(file))
    project = ctx.obj['project']
    config = ctx.obj["config"]
    if config is None:
        click.secho('create project first',
                   fg='yellow')
        return

    project.initialize_project(config)
    file_template = project.load_file_template()
    template = None
    if file == 'product':
        template = file_template.get('product_info') 
    elif file == 'product_update':
        template = file_template.get('product_update') 
    elif file == 'order':
        pass 
    elif file == 'customer':
        pass 
    elif file == 'inventory':
        template = file_template.get('inventory')  
    elif file == 'fulfillment':
        template = file_template.get('fulfillment')  
    elif file == 'supplier':
        template = file_template.get('supplier')
    elif file == 'front_shop':
        template = file_template.get('front_shop')
    elif file == 'tax':
        template = file_template.get('tax')
    elif file == 'category':
        template = file_template.get('category')
    else:
        click.echo('file template: {} not supported'.format(file))
        return 
    
    cols = []
    if type(template) is dict:
        for table, fields in template.items():
            click.echo(fields)
            fields = [table+'.'+ f for f in fields]
            cols += list(fields)
    else:
        click.echo(template)
        cols = template

    df=pd.DataFrame(columns=cols)
    df.to_csv(project.root + file + '_template.csv', index=False)
    