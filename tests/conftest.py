from click.testing import CliRunner
import pytest
from pypipet.core.project_context import PipetContext
from pypipet.core.shop_conn.shop_connector import ShopConnector
from pypipet.core.operations.utility import get_front_shop_id
from pypipet.api.app import create_app
from pypipet.api.app_celery import celery
import os

@pytest.fixture
def cli_runner():
    return CliRunner()

@pytest.fixture(scope="session")
def ctx():
    ctx = PipetContext()
    ctx.initialize_project('setting.yaml')
    ctx.set_log_level('debug')
    return ctx

@pytest.fixture(scope="session")
def session(ctx):
    sessionmaker = ctx.get_session_maker()
    session = sessionmaker()
    yield session 
    session.close()

@pytest.fixture(scope="session")
def shop_conn(ctx, session):
    shop = 'spf_site'
    shop_conn = ctx.get_shop_connector(shop) 
    
    get_front_shop_id(ctx.get_table_objects(), session, shop_conn)
    if shop_conn.front_shop_id is None:
        print(f'shop {shop} not exist')
        exit(1)
    return shop_conn


@pytest.fixture(scope="session")
def obj_classes(ctx):
    return ctx.get_table_objects()

###setup for testing flask api###
# @pytest.fixture
# def client(ctx):
#     os.environ['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
#     os.environ['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

#     app = create_app(ctx, celery=celery)
#     with app.test_client() as client:
#         yield client

# @pytest.fixture
# def api_base():
#     return '/api/v1'


