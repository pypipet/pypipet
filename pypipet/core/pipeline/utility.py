def flat_dict(d):
    flat_d = {}
    for key, val in d.items():
        if isinstance(val, dict):
            for sub_key, sub_val in val.items():
                flat_d[f'{key}.{sub_key}'] = sub_val 
        elif isinstance(val, list):
            for i, item in enumerate(val):
                for sub_key, sub_val in item.items():
                    flat_d[f'{key}.{sub_key}.{i}'] = sub_val   
        else:
            flat_d[key] = val 
    return flat_d
                
                  