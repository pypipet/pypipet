
import logging
logger = logging.getLogger('__default__')

def field_mapping(data_from:dict, data_to:dict, attr_map:dict):
    for k, val in attr_map.items():
        if type(val) is list:
            if len(data_from[k]) == 0: continue
            fields = _map_from_list(data_from[k], val)  
            data_to.update(fields) 
        elif type(val) is dict and val.get('map_to') is not None:
            mapped_value =_map_from_field(data_from[k], val)
            if mapped_value is not None:
                data_to[val['map_to']] = mapped_value
        elif type(val) is str:
            if data_from.get(k) is not None:
                data_to[val] = data_from.get(k) 



def _map_from_field(field_value, attr_map:dict):
    if attr_map.get('data_type') is not None:
        try:
            if attr_map['data_type'] == 'string':
                field_value = str(field_value)
            elif attr_map['data_type'] == 'float':
                field_value = float(field_value)
            elif attr_map['data_type'] == 'integer':
                field_value = int(field_value)
            elif attr_map['data_type'] == 'boolean':
                if attr_map.get('data_value') is not None:
                    field_value = field_value ==  attr_map['data_value']
                field_value = bool(field_value)
        except Exception as e:
            logger.debug(e)
            logger.debug([field_value])
            field_value = None 
    return field_value

def _map_from_list(data: list, attr_map_list:list):
    """
    attr_map_list [{map_from: xxx, map_to: xxx}]
    """
    res = {}
    for attr_map in attr_map_list:

        if attr_map.get('index') is not None:
            res[attr_map['map_to']] = \
                        data[attr_map['index']][attr_map['map_from']]
        elif attr_map.get('merge') is not None:
            res[attr_map['map_to']] = _merge_items(data, attr_map['map_from'], sep=',')
        elif attr_map.get('sum') is not None:
            res[attr_map['map_to']] = _sum_items(data, attr_map['map_from'])
        else:
            if  attr_map.get('condition') is not None:
                cond = list(attr_map['condition'].items())[0]
                value_dict = _search_from_list(data, cond[0], cond[1])
                if value_dict is None: continue

                map_value = value_dict.get(attr_map['map_from'])
                if map_value is None: continue
                elif type(map_value) is list:
                    map_value = '-'.join(map_value) 
                
                res[attr_map['map_to']] = map_value
            
            else:
                res[attr_map['map_to']] = data[0].get(attr_map['map_from'])
        
        if attr_map.get('data_type'):
            res[attr_map['map_to']] = _map_data_type(res[attr_map['map_to']], 
                                                     attr_map['data_type'])

    return res


def _map_data_type(val, data_type):
    try:
        if data_type == 'string':
            return str(val)
        elif data_type == 'float':
            return float(val)
        elif data_type == 'integer':
            return int(val)
        elif data_type == 'boolean':
            return bool(val)
    except Exception as e:
        logger.debug(e)
        return val 

def _search_from_list(data:[dict], key, value):
    for d in data:
        if d.get(key) == value:
            return d 
    return None

def _merge_items(data_list: [dict], key:str, sep='-'):
    items = []
    for d in data_list:
        if d.get(key) is not None:
            items.append(d[key])
    return sep.join(items)


def _sum_items(data_list: [dict], key:str):
    val = 0
    for d in data_list:
        if d.get(key) is not None:
            try:
                val += float(d[key])
            except:
                pass 
            
    return val
