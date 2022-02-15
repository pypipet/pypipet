import os

CORE_DIR = os.path.abspath(os.path.dirname(__file__))
CORE_SETTINGS = f"{CORE_DIR}/default_setting"
PROJECT_SETTING =  f"{CORE_SETTINGS}/setting.yml"
DB_SETTING = f"{CORE_SETTINGS}/db_setting.yaml"
WC_MAPPING = f"{CORE_SETTINGS}/wc_field_mapping.yaml"
SPF_MAPPING = f"{CORE_SETTINGS}/spf_field_mapping.yaml"
FILE_TEMPLATE = f"{CORE_SETTINGS}/file_template.yaml"

