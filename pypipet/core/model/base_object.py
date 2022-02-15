from copy import deepcopy

class BaseObject:
    def __init__(self, definition= None):
        if definition is None:
            self._definition = {}
        elif isinstance(definition, dict):
            self._definition = definition

    def __getattr__(self, attr: str):
        if self._definition.get(attr):
            return self._definition.get(attr, None)
        else:
            return self.__dict__[attr]

    def __repr__(self):
        return f"<{self.__class__.__name__} >"
        

    def get_attr(self, name: str):
        return self._definition.get(name, None)

    def set_attr(self, name, value):
        if name:
            self._definition[name] = value

    def set_attrs(self, attr_names: list, attr_dict: dict):
        for attr_name in attr_names:
            self.set_attr(attr_name, attr_dict.get(attr_name, None))

    def re_map(self, remap:dict):
        if remap and len(remap) > 0:
            new_definition = {}
            for field, val in self._definition.items():
                new_definition[remap.get(field, field)] = val
            self._definition = new_definition

    def get_all_attrs(self):
        return self._definition

    def trim_attrs(self):
        for k, val in self._definition.items():
            if type(val) is str:
                self.set_attr(k, val.strip())

    def set_attrs_by_table_class(self, table_obj, attrs:dict):
        cols = list(table_obj.__table__.columns.keys())
        for col in cols:
            if col == 'id': continue
            if attrs.get(col) is not None:
                self.set_attr(col, attrs[col])


    def validate_fields(self, table_obj):
        cols = list(table_obj.__table__.columns.keys())
        validated = {}
        for col in cols:
            if self._definition.get(col) is not None:
                validated[col] = self._definition[col]
        self._definition = validated

    def get_unique_attrs(self, unique_keys: list):
        unique_attrs = {}
        for k in unique_keys:
            unique_attrs[k] = self.get_attr(k)
        return unique_attrs


    
