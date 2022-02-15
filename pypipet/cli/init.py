import click 
from .cli import cli


@cli.command()
@click.argument("project_name")
@click.pass_context
def new(ctx,project_name):
    """
    initialize project
    """
    click.echo('initialize project: {}'.format(project_name))
    res = ctx.obj['project'].start_project(project_name)
    if not res:
        click.secho('project setting existed in curent dir',
                   fg='yellow',)

@cli.command()
@click.pass_context
def initialize(ctx):
    """
    initialize project
    """
    click.echo('initialize project')
    click.echo("home dir: {}".format(ctx.obj['project'].root))
    
    config = ctx.obj["config"]
    
    # print(config)
    ctx.obj['project'].initialize_project(config)
    ctx.obj['project'].import_static_data()

