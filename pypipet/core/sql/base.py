
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy import DateTime, Float
from sqlalchemy import UniqueConstraint, ForeignKeyConstraint
from sqlalchemy import Index

data_type_mapping ={
    'string': String,
    'integer': Integer,
    'bool': Boolean,
    'datetime': DateTime,
    'float': Float
}

def get_column(col:dict) -> Column:
    kwargs = {} 
    if col.get('not_null') == True:
        kwargs['nullable'] = False
    if col.get('is_key') == True:
        kwargs['primary_key'] = True
    if col.get('default'):
        kwargs['default'] = col['default']
    try:
        if col['type'] == 'string' and col.get('string_len'):
            return Column(col['name'], 
                            data_type_mapping[col['type']](col['string_len']), 
                            **kwargs)
        return Column(col['name'], 
                    data_type_mapping[col['type']], 
                    **kwargs)
    except KeyError:
        print(f"key error at db setting | {col}")
        exit(0)
  
def get_unique_constraint(constraint:dict) -> UniqueConstraint:
    """
    :param constraints: dict of unique constraint setting,
                see db_setting.yaml.
    :return:   constraint object 
    """
    return UniqueConstraint(*constraint['cols'], 
                            name=constraint['name'])


def get_foreignkey_constraint(constraint:dict) -> [ForeignKeyConstraint]:
    """
    :param constraints: dict of foreign key constraint setting,
                see db_setting.yaml.
    :return: list of constraint object 
    """
    foreign_keys = []
    for key, val in constraint.items():
        foreign_keys.append(ForeignKeyConstraint([key],[val]))
    return foreign_keys

def get_index(index_config:dict) -> Index:
    """
    :param constraints: dict of index setting,
                see db_setting.yaml.
    :return:   index object 
    """
    name ='_'.join(['idx'] +index_config['cols'])
    if index_config.get('name') is not None:
        name = index_config['name']
    return Index(name, 
                 *index_config['cols'],
                 unique=index_config['is_unique'])


