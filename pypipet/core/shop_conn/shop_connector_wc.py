
import pypipet.core.shop_conn.wc as wc
import pypipet.core.transform.wc_to_model as wc_to_model
import pypipet.core.transform.model_to_wc as model_to_wc
from .shop_connector import ShopConnector
import logging
logger = logging.getLogger('__default__')

# def _clean_up_data(data):
#     keys = set(list(data.keys()))
#     if 'created_at' in keys:
#         del data['created_at']
#     if 'updated_at' in keys:
#         del data['updated_at']


# def validate_product_info(product_info):
#     if product_info.get('images') is None:
#         logger.debug('missing images info')
#         return False

#     if product_info.get('price') is None:
#         logger.debug('missing price info')

#     if product_info.get('sku') is None:
#         logger.debug('missing sku info')

#     return True

class WCShopConnector(ShopConnector):
    def __init__(self, shop_name, shop_type, **kwargs):
        super().__init__(shop_name, shop_type, **kwargs)
        self.batch_size = kwargs.get('batch_size', 10)

    

    def add_product_to_shop(self, product_info, **kwargs):
        attr_list = kwargs.get('attr_list', ['brand', 'upc', 'size', 'color'])
        if kwargs.get('variation_attrs') is None or product_info.get('variations') is None:
            if model_to_wc.parse_to_wp_product(self.shop_api, product_info, attr_list, 
                                        status=kwargs.get('publish_type', 'publish')):
                return wc.add_product(self.shop_api, product_info)
        else:
            product = model_to_wc.parse_to_wp_product_variable(self.shop_api, product_info, 
                                            attr_list,kwargs['variation_attrs'],
                                            parent_id=kwargs.get('parent_id'))
            
            if product:
                return wc.add_product_variations(self.shop_api, product, parent_id=kwargs.get('parent_id'))


    def add_product_to_shop_bulk(self, products:list,  **kwargs):
        """for woocommerce, bulk add only for non-variable product"""
        attr_list = kwargs.get('attr_list', ['brand', 'upc', 'size', 'color'])
        batch = []
        for product_info in products:
            if model_to_wc.parse_to_wp_product(self.shop_api, product_info, attr_list):
                batch.append(product_info)
        #batch add 
        res = wc.update_product_batch(self.shop_api, 'create', batch)



    def get_destination_product_id(self, sku:str):
        """
        shop: dict with keys (front_shop_id, shop_api, shop_type)
        """
        product = wc.get_product_by_sku(self.shop_api, sku)
        if product:
            return product['id']

        return None

    def update_shop_product(self, data:dict, product_id:str, **kwargs ):
        attr_list = kwargs.get('attr_list', ['brand', 'upc', 'size', 'color'])
        if kwargs.get('formated') is None or kwargs['formated'] == False:
            if not model_to_wc.parse_to_wp_product(self.shop_api, data, attr_list, update_only=True):
                logger.debug('wp parsing failed')
                return 
        # print(data)
        if kwargs.get('parent_id') is not None:
            # print(kwargs['parent_id'], data)
            return wc.update_variation(self.shop_api, kwargs['parent_id'], product_id, data)
        return wc.update_product(self.shop_api, product_id, data)

    def update_shop_product_batch(self, data:list, **kwargs):
        attr_list = kwargs.get('attr_list', ['brand', 'upc', 'size', 'color'])
        batch = []
        for i, d in enumerate(data):
            # print(d)
            if kwargs.get('formated') is None or kwargs['formated'] == False:
                if model_to_wc.parse_to_wp_product(self.shop_api, d, attr_list, update_only=True):
                    if d.get('parent_id') is not None:
                        # print(d)
                        wc.update_variation(self.shop_api, d['parent_id'] , d['id'], d)
                    else:
                        batch.append(d)
            else:
                batch.append(d)
        
        res = wc.update_product_batch(self.shop_api, 'update', batch)
        return res

    def sync_shop_orders(self,  **kwargs):
        res = []
        wp_orders = wc.get_new_orders(
            self.shop_api,
            start_from_order=kwargs.get('latest_order_id', '0'), 
            page_start=kwargs.get('page_start', 1), 
            per_page=kwargs.get('per_page', 20))
    
        for order in wp_orders:
            print('prcessing order', order['id'])
            # todo: get tax based on geo
            data = wc_to_model.wp_parse_order(order, 
                            kwargs.get('field_mapping', self.field_mapping), 
                            shipping_tax_id=kwargs.get('shipping_tax_id',2), 
                            item_tax_id=kwargs.get('item_tax_id', 1)) 
            res.append(data)

        return res


    def update_order_status_at_shop(self, destination_order_id, 
                                   status,**kwargs):
        res = wc.update_order(self.shop_api,
                            destination_order_id,
                            data={'status': status})
        return res

    def update_order_at_shop(self, destination_order_id, 
                             data, **kwargs):
        res = wc.update_order(self.shop_api,
                            destination_order_id,
                            data=data)
        return res

    def update_order_item_at_shop(self, destination_order_id, 
                             items, **kwargs):
        order = wc.get_order_by_id(self.shop_api,
                                   destination_order_id)
        item_list = model_to_wc.transform_order_item(order, items)
        # print(item_list)
        res = wc.update_order(self.shop_api,
                            destination_order_id,
                            data={'line_items': item_list})
        return res

    def get_order_at_shop(self, **kwargs):
        # print(kwargs.get('destination_order_id'))
        res = wc.get_order_by_id(self.shop_api,
                            kwargs.get('destination_order_id'))
        # todo: get tax based on geo
        res = wc_to_model.wp_parse_order(res, kwargs.get('field_mapping', self.field_mapping), 
                        shipping_tax_id=kwargs.get('shipping_tax_id',2), 
                        item_tax_id=kwargs.get('item_tax_id', 1)) 
        return res

            

    def get_products_at_shop(self, **kwargs):
        """wc page start from 1"""
        data = wc.list_products(self.shop_api, 
                            params={
                                'page': kwargs.get('page', 1), 
                                'per_page': kwargs.get('batch_size', 10),
                                'status': kwargs.get('status', 'publish')
                            }) 
        for i, d in enumerate(data):
            data[i] = self._parse_product(d, 
                                    kwargs.get('field_mapping', self.field_mapping))
        return data
                
                            
    def get_product_at_shop(self, product_id, **kwargs):
        res = wc.get_product_by_id(self.shop_api, product_id) 
        return self._parse_product(res, 
                                    kwargs.get('field_mapping', self.field_mapping))
            
                

    def get_category_taxonomy(self, **kwargs):
        page = 1
        cats = []
        while True:
            batch_cats = wc.list_categories(self.shop_api, 
                                    page, 
                                    params=kwargs) 
            if batch_cats is None:
                return None
            if len(batch_cats) == 0:
                break
            cats += batch_cats 
            page += 1
        wc_to_model.wp_category_to_taxonomy(cats)
        return cats
    
    def update_customer_at_shop(self, destination_order_id, 
                             data, **kwargs):
        model_to_wc.transform_customer(data)
        update = {}
        if kwargs.get('is_billing'):
            update['billing'] = data
        elif kwargs.get('is_shipping'):
            update['shipping'] = data
        else:
            logger.debug('need to specify biling or shipping')
            return 
        return wc.update_order(self.shop_api, destination_order_id, update) 

    def add_tracking(self, destination_order_id, 
                            message, **kwargs):
        assert message.get('tracking_id')
        assert message.get('provider')
        tracking = f"tracking code {message['tracking_id']} service by \
                        {message['provider']}"
        res = wc.send_wc_message(self.shop_api,
                            destination_order_id,
                            tracking)
        return res

    def send_message(self, destination_order_id, 
                            message, **kwargs):
        res = wc.send_wc_message(self.shop_api,
                            destination_order_id,
                            message)
        return res

    def _parse_product(self, product, field_mapping):
        parsed = wc_to_model.parse_product(product, field_mapping)
        if parsed == 0:
            return 
        elif parsed == 1:
            variations = []
            for pid in product['variations']:
                vari = wc.get_product_by_id(self.shop_api, pid) 
                if vari: variations.append(vari)
            product['variations'] = variations 
            
            parsed = wc_to_model.parse_product_with_variations(product, field_mapping)
            
        return parsed
