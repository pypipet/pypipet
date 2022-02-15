import os
from .db import project_engine, import_data
from .config_service import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base
from pypipet.plugins.woocommerce.api import API as WC_API
import shopify as SHOPIFY_API
from pypipet.core.logging import setup_logging
from pypipet.core.fileIO.file_loader import read_yml_file
from pypipet.core.fileIO.file_saver import write_yaml
from pypipet.core.shop_conn.shop_connector_wc import WCShopConnector
from pypipet.core.shop_conn.shop_connector_shopify import SPFShopConnector
from pypipet.core.shop_conn.spf_auth import start_session
from .config import *
import logging
logger = logging.getLogger('__default__')

class PipetContext():
    def __init__(self, *args, **kwargs):
        self.engine = kwargs.get('engine', None)
        self.table_objects = kwargs.get('engine', None)
        self.root = kwargs.get('root_path', os.getcwd())
        if not self.root.endswith('/'):
            self.root += '/'
        self.config = None
        self.db_config = None
        self._shop_connectors = {}

    def start_project(self, project_name, **kwargs):
        if os.path.isfile(self.root + 'setting.yaml'):
            return False 
        project_setting = read_yml_file(PROJECT_SETTING)
        project_setting['project_setting']['name'] = project_name
        project_setting['project_setting']['home_dir'] = self.root
        # project_setting['project_setting']['attr_list'] = ['brand', 'upc', 'size', 'color']

        write_yaml(project_setting,
                   self.root + 'setting.yaml')

        os.makedirs(self.root + 'bundle', exist_ok=True)
        db_setting = read_yml_file(DB_SETTING)
        write_yaml(db_setting,
                   self.root + 'bundle/db_setting.yaml')

        wc_mapping = read_yml_file(WC_MAPPING)
        write_yaml(wc_mapping,
                   self.root + 'bundle/wc_field_mapping.yaml')

        wc_mapping = read_yml_file(SPF_MAPPING)
        write_yaml(wc_mapping,
                   self.root + 'bundle/spf_field_mapping.yaml')

        file_template = read_yml_file(FILE_TEMPLATE)
        write_yaml(file_template,
                   self.root + 'bundle/file_template.yaml')
        return True

    def initialize_project(self, config_file=None):
        if self.config is None:
            self.config = read_yml_file(config_file)['project_setting']
       
        if self.db_config is None:
            self.db_config = read_yml_file(
                     self.config['home_dir'] \
                    + self.config['databse_setting'])
            is_valid, message = validate(self.db_config)

            if not is_valid:
                logger.info(message)
                return 
            
        
        if self.engine is None:
            self.engine = project_engine(self.db_config)

        if self.engine:
            self.set_table_objects(self.engine)
            self._session_maker = sessionmaker(bind=self.engine)
            self._initialize_shops()

    def _initialize_shops(self):
        for shop_name, shop_config in self.config['shops'].items():
            if shop_config['site_type'] == 'wc':
                shop_conn = WCShopConnector(shop_name, 
                            shop_config['site_type'],
                            batch_size=shop_config['batch_size']) 
                self.set_wc_mapping()
                api = WC_API(
                    url=shop_config['url'],
                    consumer_key=shop_config['consumer_key'],
                    consumer_secret=shop_config['consumer_secret'],
                    version=shop_config['version']
                  )

                shop_conn.set_shop_api(api)
                self.set_shop_connector(shop_name, shop_conn)
            elif shop_config['site_type'] == 'shopify':
                is_private_app = shop_config.get('private_app_password') is not None
                api_session = start_session(
                                            private_app=is_private_app,
                                            **shop_config)
                
                shop_conn = SPFShopConnector(shop_name,
                            shop_config['site_type'])
                shop_conn.set_shop_api(api_session)

                self.set_spf_mapping()
                self.set_shop_connector(shop_name, shop_conn)
                # shopify.ShopifyResource.activate_session(session)

    def get_session_maker(self):
        if self.engine:
            if self._session_maker:
                return self._session_maker
            self._session_maker = sessionmaker(bind=self.engine)
            return self._session_maker
        return None
    
    def set_log_level(self, log_level, path='./'):
        self.log_level = log_level
        setup_logging(log_level, log_path=path)


    def set_table_objects(self, engine):
        base = automap_base()
        base.prepare(engine, reflect=True)
        self.table_objects = base.classes 

    def get_table_objects(self):
        return self.table_objects

    def get_table_columns(self, table_name):
        if self.table_objects.get(table_name):
            return self.table_objects.get(table_name).__table__.columns.keys()

    
    def set_shop_connector(self, name, connector):
        if connector.shop_type == 'wc':
            connector.set_field_mapping(self.get_wc_mapping())
        elif connector.shop_type == 'shopify':
            connector.set_field_mapping(self.get_spf_mapping())
        self._shop_connectors[name] = connector

    def get_shop_connector(self, name):
        return self._shop_connectors.get(name, None)

    def set_wc_mapping(self):
        self._wc_mapping = load_mapping(
                 filename=self.root + self.config['wc_field_mapping'])

    def get_wc_mapping(self):
        return self._wc_mapping.get('mapping')

    def set_spf_mapping(self):
        self._spf_mapping = load_mapping(
                 filename=self.root + self.config['spf_field_mapping'])

    def get_spf_mapping(self):
        return self._spf_mapping.get('mapping')

    def import_static_data(self):
        session = self._session_maker()
        settings = self.db_config
                
        if settings and settings.get('manual_data_input'):
            import_data(self.get_table_objects(), 
                       session, 
                       settings.get('manual_data_input'))
        session.close()
    

    def load_file_template(self):
        return read_yml_file(self.config['file_template'])
    
    