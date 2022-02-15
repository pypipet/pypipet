from .base_object import BaseObject
from .customer import Customer
from pypipet.core.sql.query_interface import get_product_by_destination
import re

class OrderItem(BaseObject):
    __table_name__ = 'order_item'
    def __init__(self, attrs: dict = None):
        super().__init__(attrs)
    
    def set_order_item(self, table_objs, attrs: dict):
        self.set_attrs_by_table_class(table_objs.get(self.__table_name__), 
                                     attrs)
    def get_order_item_info(self, **kwargs):
        table_objs = kwargs.get('table_objs')
        session = kwargs.get('session')
        params = {}
        if self.destination_id is not None:
            params['id'] = self.destination_id
        else:
            params.update({
                        'front_shop_id':  self.front_shop_id,
                        'destination_product_id':  str(self.destination_product_id)
                    })
        product_info = get_product_by_destination(
                table_objs, 
                session, 
                params
                )
        product_info.update(params)
        return product_info



class Order(BaseObject):
    __table_name__ = 'shop_order'
    def __init__(self, attrs: dict = None):
        super().__init__(attrs)
        self.order_items = []
        self.billing_customer = None
        self.shipping_customer = None
        self.trackings = None

    def set_order(self, table_objs, attrs: dict):
        self.set_attrs_by_table_class(table_objs.get(self.__table_name__), 
                                     attrs)
        if attrs.get('order_item'):
            for item_data in attrs['order_item']:
                item = OrderItem()
                item.set_attrs_by_table_class(
                            table_objs.get(item.__table_name__), 
                            item_data)
                self.order_items.append(item)
        if attrs.get('shipping_customer'):
            customer = Customer()
            customer.set_attrs_by_table_class(
                            table_objs.get(customer.__table_name__), 
                            attrs['shipping_customer'])
            self.shipping_customer = customer

        if attrs.get('billing_customer'):
            customer = Customer()
            customer.set_attrs_by_table_class(
                            table_objs.get(customer.__table_name__), 
                            attrs['billing_customer'])
            self.billing_customer = customer

        if attrs.get('fulfillment'):
            self.trackings = attrs['fulfillment']

    def update_order_id(self, shop_order_id):      
        self.set_attr('id', shop_order_id) 
        for item in self.order_items:
            item.set_attr('shop_order_id', shop_order_id)
        if self.trackings:
            for i, tracking in enumerate(self.trackings):
                self.trackings[i]['shop_order_id'] = shop_order_id

    def get_order_items(self):
        pass

    def get_shipping(self):
        pass

    def get_customer(self):
        pass


    def get_issues(self):
        pass

    def get_order_info(self, **kwargs):
        info = self.get_all_attrs()
        info['order_items'] = []
        for item in self.order_items:
            if kwargs.get('item_info') == True:
                info['order_items'].append(item.get_order_item_info(**kwargs))
            else:
                info['order_items'].append(item.get_all_attrs())
        info['billing'] = self.billing_customer.get_all_attrs()
        info['shipping'] = self.shipping_customer.get_all_attrs()
        return info

# class Fulfillment(BaseObject):
#     __table_name__ = 'fulfillment'
#     def __init__(self, attrs: dict = None):
#         super().__init__(attrs)

#     def set_fulfillment(self, table_objs, attrs: dict):
#         self.set_attrs_by_table_class(table_objs.get(self.__table_name__), 
#                                      attrs)

#     def update_status(self):
#         pass

#     def update_tracking(self, tracking: dict=None):
#         if self.get_attr('tracking_id') is None:
#             self.tracking_id = tracking.get('tracking_id', None)
#             self.provider = tracking.get('provider', None)
#         else:
#             if tracking.get('tracking_id', None) != self.tracking_id:
#                 self.tracking_id = tracking.get('tracking_id', None)
#                 self.provider = tracking.get('provider', None)

#         # return self.validate_tracking_id()

#     def validate_tracking_id(self):
#         return
                    


        