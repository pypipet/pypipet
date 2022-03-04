
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import inspect, text, Table,DateTime
from sqlalchemy.sql import func
from sqlalchemy import MetaData
import datetime, logging
from .base import *
import logging
logger = logging.getLogger('__default__')

def init_tables(engine, table_settings:dict, schema=None):
    base = None 
    if schema is None:
        base = declarative_base()
    else:
        logger.debug(f'db operation on schema {schema}')
        base = declarative_base(metadata=MetaData(schema=schema))
    base.metadata.reflect(engine)
    
    for name, config in table_settings.items():
        search_name = name
        if schema is not None:
            search_name = f'{schema}.{name}'
        if base.metadata.tables.get(search_name) is None:
            # logging.debug(f"Creating table {name}")
            table = create_table(name, config, base.metadata)
           
    base.metadata.create_all(engine)

def drop_all_tables(table_settings, engine, schema=None):
    #quickly drop tables in dev
    base = None 
    if schema is None:
        base = declarative_base()
    else:
        logger.debug(f'db operation on schema {schema}')
        base = declarative_base(metadata=MetaData(schema=schema))
    base.metadata.reflect(engine)
    tables = []
    for name, config in table_settings.items():
        if schema is not None:
            name = f'{schema}.{name}'
        table = base.metadata.tables.get(name)
        if table is not None:
            tables.append(table)
    
    i = 0
    table = tables[i]
    from random import randrange
    while True:
        try:
            table.drop(engine)
            logger.debug(f"drop {table}, len {len(tables)}")
            tables.pop(i)
        except:
            pass
        if len(tables) == 0:
            break
        i = randrange(len(tables))
        table = tables[i]
        
        
   
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

