"""Defines helpers related to the system database."""

import logging
import time

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

from .errors import DialectNotSupportedError
from .sql.init_db import *
from .sql.query_interface import insert_list_raw


def project_engine(db_setting):
    """Creates and register a SQLAlchemy engine"""
    engine_uri = dialect_engine_uri(db_setting['db_setting']['db_type'],
                       db_setting['db_setting']['db_conn'])
    logging.debug(f"Creating engine {engine_uri}")
    engine = create_engine(engine_uri, pool_pre_ping=True)

    check_db_connection(
        engine,
        max_retries=db_setting['db_setting'].get("database_max_retries"),
        retry_timeout=db_setting['db_setting'].get("database_retry_timeout"),
    )
    
    init_tables(engine, db_setting['db_setting']['tables'])

    return engine

def dialect_engine_uri(dialect, params={}):
        # engine_uri according to the db type
        db_suffix = lambda s: str(Path(s).with_suffix(".db"))

        dialect_templates = {
            "postgres": lambda params: "postgresql://{user}:{password}@{host}:{port}/{dbname}".format(
                **params
            ),
            "snowflake": lambda params: "snowflake://{username}:{password}@{account}/{database}/{schema}?warehouse={warehouse}&role={role}".format(
                **params
            ),
            "sqlite": lambda params: "sqlite:///{database}".format(
                database=db_suffix(params.pop("database")), **params
            ),
        }

        try:
            url = dialect_templates[dialect](
                params
            )

            return url
        except KeyError:
            raise DialectNotSupportedError(dialect)

def check_db_connection(engine, max_retries, retry_timeout):  
    """Check if the database is available the first time a project's engine is created."""
    attempt = 0
    while True:
        try:
            engine.connect()
        except OperationalError:
            if attempt == max_retries:
                logging.error(
                    "Could not connect to the Database. Max retries exceeded."
                )
                raise
            attempt += 1
            logging.info(
                f"DB connection failed. Will retry after {retry_timeout}s. Attempt {attempt}/{max_retries}"
            )
            time.sleep(retry_timeout)
        else:
            break


def import_data(table_objs, session, input_tables: dict):
    for tablename, data in  input_tables.items():
        insert_list_raw( table_objs.get(tablename), 
                         session,
                          data)


def set_schema(session, dialect, schema_name):
    if schema_name is None:
        return
    if dialect == 'oracle':
        session.execute(text(f'ALTER SESSION SET CURRENT_SCHEMA={schema_name}'))
    elif dialect == 'postgres':
        session.execute(text(f'SET search_path={schema_name}'))

def add_schema(session, dialect, schema_name):
    if schema_name is None:
        return 
    create_schema = None
    if dialect == 'postgres':
        create_schema = text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
    
    if create_schema is not None:
        print(create_schema)
        session.execute(create_schema)
        session.commit()
            
