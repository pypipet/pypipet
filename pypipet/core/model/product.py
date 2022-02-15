from .base_object import BaseObject
from pprint import pprint
import logging
logger = logging.getLogger('__default__')


class Inventory(BaseObject):
    __table_name__ = 'inventory'
    def __init__(self, attrs: dict = None):
        super().__init__(attrs)


    def set_inventory(self, table_objs, attrs: dict):
        self.set_attrs_by_table_class(table_objs.get(self.__table_name__), 
                                     attrs)

class Destination(BaseObject):
    __table_name__ = 'destination'
    def __init__(self, attrs: dict = None):
        super().__init__(attrs)

    def set_destination(self, table_objs, attrs: dict):
        self.set_attrs_by_table_class(table_objs.get(self.__table_name__), 
                                     attrs)
    def print_destination(self):
        print('destinations')
        pprint(self.get_all_attrs())
    # def set_destination(self, attr_names: dict, attrs: dict):
    #     if attr_names.get('destination'):
    #         self.set_attrs(attr_names['destination'], attrs)

class Variation(BaseObject):
    __table_name__ = 'variation'
    def __init__(self, attrs: dict = None):
        super().__init__(attrs)
        self.destinations = []

    # def get_variation(self):
    #     variation = self.get_all_attrs()
    #     if self.destinations:
    #         variation['destinations'] = []
    #         for dest in self.destinations:
    #             variation['destinations'].append(dest.get_destination())
    #     return variation


    def set_variation(self, table_objs, attrs: dict):
        self.set_attrs_by_table_class(table_objs.get(self.__table_name__), 
                                     attrs)
        if attrs.get('destinations'):
            for dest_data in attrs['destinations']:
                dest = Destination()
                dest.set_destination(
                                        table_objs, 
                                        dest_data)
                self.destinations.append(dest)

    def print_variation(self):
        print('variations')
        pprint(self.get_all_attrs())
        for dest in self.destinations:
            dest.print_destination()
    # def add_to_shop(self, front_shop:dict, data:dict):
    #     """"
    #     add variation to front shop
    #     front_shop: shop type and api 
    #     data: destination attrs
    #     """
    #     if self.sku is None:
    #         logger.debug('missing sku')
    #         return None 
    #     data['sku'] = self.sku

    #     if data.get('price') is None:
    #         logger.debug('missing price')
    #         return None
    #     if data.get('destination_product_id') is None \
    #                                 and front_shop is None:
    #         logger.debug('missing  product id at front_shop')
    #         return None

    #     if data.get('destination_product_id') is None:
            # data['destination_product_id'] = get_destination_product_id(
    #             front_shop, self.sku
    #         )

    #     destination = Destination(data)



class Product(BaseObject):
    __table_name__ = 'product'
    def __init__(self, attrs: dict = None):
        super().__init__(attrs)
        self.variations = []
        self.category = None

    def get_product(self):
        product = self.get_all_attrs() 
        if self.variations:
            product['variations'] = []
            for vari in self.variations:
                product['variations'].append(vari.get_variation())
        return product

    def set_product(self, table_objs, attrs: dict):
        """
        set up product object
        :table_objs: table classes
        :attrs: dict - data dict
        """
        self.set_attrs_by_table_class(table_objs.get(self.__table_name__), 
                                     attrs)
        if attrs.get('category'):
            category = Category()
            category.set_category(table_objs, 
                                attrs['category'])
            self.category = category
        if attrs.get('variations'):
            for vari in attrs['variations']:
                variation = Variation()
                if vari.get('sku'):
                    vari['sku'] = str(vari['sku'])
                variation.set_attrs_by_table_class(
                                        table_objs.get(variation.__table_name__), 
                                        vari)
                self.variations.append(variation)

    def update_product_id(self, product_id):
        self.set_attr('id', product_id)
        for vari in self.variations:
            vari.set_attr('product_id', product_id)

    def print_product(self):
        print('product')
        pprint(self.get_all_attrs())
        for vari in self.variations:
            vari.print_variation()

     
class Category(BaseObject):
    __table_name__ = 'category'
    def __init__(self, attrs: dict = None):
        super().__init__(attrs)

    def get_parent(self, sep='>') -> str:
        """
        :param sep: seperator in full path.
        :return:   parent category: str 
        """
        if self.full_path:
            categories = self.full_path.split(sep)
            if len(categories) < 2:
                return None
            self.set_attr('parent', categories[-2].strip())
            return self.parent

        return None   

    def validate(self, sep='>'):
        """
        :param sep: seperator in full path.
        :return:   parent category: str 
        """
        if self.category and self.category.strip() != '':
            return True 
        if self.full_path and self.full_path.strip() != '':
            self.get_parent(sep=sep)
        return False   

    def set_category(self, table_objs, attrs: dict):
        if type(attrs) is dict:
            self.set_attrs_by_table_class(table_objs.get(self.__table_name__), 
              attrs)
        elif type(attrs) is str:
            self.category = attrs


#to do remove this class
class Tax(BaseObject):
    def __init__(self, attrs: dict = None):
        super().__init__(attrs)
        
    def override_tax_rate(self, rate):
        self.set_attr('override_rate', rate)
            
class FrontShop(BaseObject):
    def __init__(self, attrs: dict = None):
        super().__init__(attrs)
        api_conn = None

    def get_api(self):
        pass

#to do remove this class
class SupplierInvoice(BaseObject):
    def __init__(self, attrs: dict = None):
        super().__init__(attrs)

    def get_supplier(self):
        pass

    def set_invoice(self, attr_names: dict, attrs: dict):
        if attr_names.get('supplier_invoice'):
            self.set_attrs(attr_names['supplier_invoice'], attrs)