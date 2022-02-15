from pypipet.core.operations.order import add_orders_to_db_bulk
from pypipet.core.fileIO.file_saver import write_csv_file
from pypipet.core.operations.inventory import update_inventory_bulk
from pypipet.core.operations.inventory import match_variation_sku_by_upc
from pypipet.core.operations.inventory import update_instock_qty_db
from pypipet.core.operations.inventory import update_instock_front_shop
from pypipet.core.operations.frontshop import update_front_shop_price_bulk
from .utility import *

class Action():
    def __init__(self, name, params:dict=None, **kwargs):
        self.name = name 
        if params is None: params = {}
        self.params = params
        if kwargs.get('func'):
            self.func = kwargs['func']

    def run_external_func(self, data, params:dict):
        return self.func(data, **params)


class ActionMap():
    def __init__(self):
        pass

    @staticmethod
    def mapping(data: list, action):
        if action.name == 'add_orders_to_db':
            add_orders_to_db_bulk(
                action.params.get('table_objs'),
                action.params.get('session'),
                data,
                action.params.get('shop_connector').front_shop_id
            ) 
            return data
        elif action.name == 'model_to_dict':
            if action.params.get('model_name') == 'order':
                data = [order.get_order_info() for order  in data]
            else:
                data = [d.get_all_attrs() for d in data]
            data = [flat_dict(d) for d in data]
            return data
        elif action.name == 'update_inventory_to_db':
            update_inventory_bulk(
                action.params.get('table_objs'),
                action.params.get('session'),
                data
            )
            return data
        elif action.name == 'match_inventory_sku':
            match_variation_sku_by_upc(
                action.params.get('table_obj'),
                action.params.get('session'),
                data
            )
            return data
        elif action.name == 'update_instock_qty_db':
            update_instock_qty_db(
                action.params.get('table_objs'),
                action.params.get('session'),
                batch_size=action.params.get('batch_size'),
                params=action.params.get('params', {})
            )
            return data
        elif action.name == 'update_instock_qty_shop':
            update_instock_front_shop(
                action.params.get('table_objs'),
                action.params.get('session'),
                action.params.get('shop_connector'),
                batch_size=action.params.get('batch_size'),
                params=action.params.get('params', {})
            )
            return data
        # elif action.name == 'sync_order_item_from_shop':
        #     update_order_items_from_shop(
        #         action.params.get('table_objs'),
        #         action.params.get('session'),
        #         action.params.get('shop_connector'),
        #         data)
            
        #     return data
        elif action.name == 'update_front_shop_price':
            update_front_shop_price_bulk(
                action.params.get('table_objs'),
                action.params.get('session'),
                action.params.get('shop_connector'),
                data)
            
            return data

        elif action.name == 'save_to_csv':
            write_csv_file(data, 
                           action.params.get('save_to', 
                                            'pp_save_to_csv.csv'))
            return data
    
    