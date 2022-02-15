import click 
from .cli import cli
# from pypipet.api.app import create_app

@cli.command()
@click.argument("action",  type=click.Choice(['start', 'stop']))
@click.pass_context
def api(ctx, action):
    """
    run flask api
    """
    click.echo('running flask api')
    project = ctx.obj['project']
    config = ctx.obj["config"]
    if config is None:
        click.secho('create project first',
                   fg='yellow')
        return

    project.initialize_project(config)
    # app = create_app(project)
    # app.run(debug=True)

    