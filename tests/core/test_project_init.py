
from unittest.mock import Mock
import pytest
from pypipet.core.project_context import PipetContext
from sqlalchemy.exc import OperationalError
import os


class TestProjectInit:
    def test_init_project(self):
        ctx = PipetContext()
        ctx.start_project('test')
        assert ctx.root is not None
    
    def test_start_project(self):
        ctx = PipetContext()
        ctx.start_project('test')
        setting_file = ctx.root + 'setting.yaml'
        assert os.path.isfile(setting_file) is not None 
        

        ctx.initialize_project(config_file=setting_file)
        assert ctx.config is not None 
        assert ctx.db_config is not None
        assert ctx.config.get('file_template') is not None
        assert ctx.engine is not None


        assert ctx.get_session_maker() is not None 
        
        ctx.set_log_level('debug')
        assert ctx.log_level is not None 

        ctx.import_static_data()

        