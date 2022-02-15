
import pypipet.core.shop_conn.wc as wc
import pypipet.core.transform.wc_to_model as wc_to_model
import pypipet.core.transform.model_to_wc as model_to_wc


class ShopConnector(object):
    def __init__(self, shop_name, shop_type, **kwargs):
        self.shop_name = shop_name
        self.shop_type = shop_type
        self.shop_api = kwargs.get('api', None)
        self.front_shop_id = kwargs.get('front_shop_id', None)
        self.field_mapping = kwargs.get('field_mapping', None)
        

    def set_shop_api(self, api):
        self.shop_api = api 

    def set_front_shop_id(self, shop_id):
        self.front_shop_id = shop_id

    def set_field_mapping(self, mapping):
        self.field_mapping = mapping

    def get_shop_info(self):
        return {
            'shop_name': self.shop_name,
            'shop_type': self.shop_type,
            'front_shop_id': self.front_shop_id
        }


    def add_product_to_shop(self,product_info: dict, **kwargs):
        pass

    def add_product_to_shop_bulk(self, products:list,  **kwargs):
        pass


    def update_shop_product(self, data:dict, product_id:str, **kwargs ):
        pass

    def update_shop_product_batch(self, data:list, **kwargs):
        pass

    def sync_shop_orders(self,**kwargs):
        pass

    def update_order_status_at_shop(self, destination_order_id: str, 
                                   status: str,**kwargs):
        pass

    def update_order_at_shop(self, destination_order_id: str, 
                             data, **kwargs):
        pass

    def update_order_item_at_shop(self, destination_order_id: str, 
                             items: list, **kwargs):
        pass

    def get_order_at_shop(self, **kwargs):
        pass

        
    def get_products_at_shop(self,**kwargs):
        pass
                                    
    def get_product_at_shop(self, product_id: str, **kwargs):
        pass
    
    def get_category_taxonomy(self, **kwargs):
        pass
    
    def update_customer_at_shop(self,destination_order_id: str, 
                             data: dict, **kwargs):
        pass 

    def add_tracking(self,destination_order_id: str, 
                            message: dict, **kwargs):
        pass

    def send_message(self, destination_order_id: str, 
                            message: str, **kwargs):
        pass


