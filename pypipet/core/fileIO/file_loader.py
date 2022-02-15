import pandas as pd
import yaml

def read_file_to_df(filename, params:dict=None):
    if params is None: params = {}
    if filename.endswith('.xlsx'):
        return read_excel_file(
                filename,
                sheet_name=params.get('sheet_name', 'Sheet1'))
    elif filename.endswith('.csv'):
        return read_csv_file(filename)


def read_csv_file(filename):
    return pd.read_csv(filename,
                header = 0, 
                dtype=str,
                keep_default_na=False)

def read_excel_file(filename, sheet_name='Sheet1'):
    return pd.read_excel(filename,
                header = 0, 
                dtype=str,
                keep_default_na=False,
                sheet_name=sheet_name)

def read_yml_file(filename):
    data = None 
    with open(filename, 'r') as f:
        data = yaml.safe_load(f)
    return data