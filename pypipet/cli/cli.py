import click 
from pypipet.core.logging import LEVELS
from pypipet.core.project_context import PipetContext

@click.group(invoke_without_command=True, no_args_is_help=True)
@click.option("--log-level", type=click.Choice(LEVELS.keys()), 
                             default='debug')
@click.option("--log-path", default='./')
@click.option("-v", "--verbose", count=True)
@click.option("-conf", "--config", default='setting.yaml')
@click.pass_context
def cli(ctx, log_level, log_path, verbose, config):
    """
    Get help at https://abc
    """
    #init context
    project = PipetContext()

    ctx.ensure_object(dict)
    ctx.obj["verbosity"] = verbose

    ctx.obj["config"] = config

    if ctx.obj.get("project") is None:
        ctx.obj["project"] = project
        if config == 'setting.yaml':
            ctx.obj["config"] = ctx.obj['project'].root + config

    if log_level:
        project.set_log_level(log_level, log_path)
        
    click.echo(project.log_level)
    