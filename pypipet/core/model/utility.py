def map_attr_names(data: dict, field_map: dict):
    "map dict name to alias"
    mapped = {}
    for k, val in data.items():
        mapped_k = field_map.get(k, k)
        mapped[mapped_k] = val
    return mapped

def get_unique_attrs(data: dict, unique_keys:list):
    unique = {}
    for k in unique_keys:
        if data.get(k):
            unique[k] = data[k]
    return unique