
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import inspect, text, Table,DateTime
from sqlalchemy.sql import func
import datetime, logging
from .base import *
import logging
logger = logging.getLogger('__default__')

def init_tables(engine, table_settings:dict):
    base = declarative_base()
    base.metadata.reflect(engine)

    for name, config in table_settings.items():
        if base.metadata.tables.get(name) is None:
            logging.debug(f"Creating table {name}")
            table = create_table(name, config, base.metadata)
            logging.debug(f'created table {name}')

    base.metadata.create_all(engine)

def drop_all_tables(table_settings, engine):
    #quickly drop tables in dev
    base = declarative_base()
    base.metadata.reflect(engine)
    tables = []
    for name, config in table_settings.items():
        table = base.metadata.tables.get(name)
        if table is not None:
            tables.append(table)

    for i in range(1, len(tables)+1):
        table = tables[-i]
        table.drop(engine)
    return tables



def create_table(table_name, config:dict, meta:declarative_base):
    """create a table
    (setting on db_setting.yaml)"""
    logger.debug(f'creating table {table_name}')
    args = []
    for col in config['columns']:
        args.append(get_column(col)) 

    # add created_at and updated_at
    args.append(
        Column('created_at',
         DateTime,  
        nullable=False, server_default=func.now())
    )
    args.append(
         Column('updated_at',
         DateTime, 
         onupdate=func.now(),
         default=func.now()
         )
    )
    #add constraints
    if config.get('unique_constraint'):
        for conf in config['unique_constraint']:
            args.append(get_unique_constraint(conf))
    if config.get('foreign_key_constraint'):
        args += get_foreignkey_constraint(config['foreign_key_constraint'])
  
    #add index
    if config.get('index'):
        for conf in config['index']:
            args.append(get_index(conf))
    
    return Table(table_name,
                  meta,
                  *args)

