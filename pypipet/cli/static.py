import click 
from .cli import cli
from pypipet.core.operations.static import get_static_data
from pypipet.core.operations.static import add_static_data
from pypipet.core.operations.static import edit_static_data
from pypipet.core.fileIO.file_loader import read_csv_file

@cli.command()
@click.argument("action",  type=click.Choice(['add', 'edit', 'show']))
@click.option("--target", type=click.Choice(['supplier', 'front_shop', 'tax', 'category']))
@click.option("-f", "--filename",
                help=" add/edit  in bulk")
@click.pass_context
def Static(ctx, action, target, filename):
    """
    add/edit stastic data (supplier, tax, category, frontshop)
    """
    click.echo('{} {} ...'.format(action, target))

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

    if action == 'add':
        _add_data(session, table_classes, target, filename)
    elif action == 'edit':
        _edit_data(session, table_classes, target, filename)
    elif action == 'show':
        _show_data(session, table_classes, target)
    else:
        click.secho('action not supported: {}'.format(action),
                fg='yellow')
    
    session.close()

def _show_data(session, table_classes, target):
    data = get_static_data(table_classes.get(target), session)
    if data is not None:
        for d in data:
            click.echo(d) 
    else:
        click.secho('can not get data: {}'.format(taret),
                fg='yellow')

def _add_data(session, table_classes, target, filename):
    data = _get_data_from_file(filename, target) 
    for d in data:
        click.echo('adding {} {}'.format(target, d))
        add_static_data(table_classes.get(target), session, d)


def _edit_data(session, table_classes, target, filename):
    data = _get_data_from_file(filename, target)
    for d in data:
        click.echo('editing {} {}'.format(target, d))
        edit_static_data(table_classes, session, d, target)


def _get_data_from_file(filename, target):
    data = read_csv_file(filename)
    res = []

    #validation
    for i, row in data.iterrows():
        if (target in ['supplier', 'front_shop', 'tax'] and row['name'].strip() == '') \
        or (target in ['category'] and row['category'].strip() == ''):
            click.secho('row {} missing name , \
             stop processing'.format(i+1), 
                        fg='yellow')
            return 
        res.append(dict(row))

    return res