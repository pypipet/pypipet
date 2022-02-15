import click, logging
from .cli import cli
from pypipet.core.logging import setup_logging

from . import ( 
    init,
    catalog,
    product,
    template,
    order,
    inventory,
    fulfillment,
    static,
    api
)
