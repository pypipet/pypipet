from .base_object import BaseObject


class Customer(BaseObject):
    __table_name__ = 'customer'
    def __init__(self, attrs: dict = None):
        super().__init__(attrs)
    
    def set_customer(self, table_objs, attrs: dict):
        self.set_attrs_by_table_class(table_objs.get(self.__table_name__), 
                                     attrs)

    def get_issues(self):
        pass 

    def add_issues(self):
        pass
            
    
