
from dataclasses import field
import pypipet.core.shop_conn.spf as spf
from pypipet.core.sql.query_interface import add_new_product
import pypipet.core.transform.spf_to_model as spf_to_model
import pypipet.core.transform.model_to_spf as model_to_spf
from .shop_connector import ShopConnector
import shopify
import logging
logger = logging.getLogger('__default__')

class SPFShopConnector(ShopConnector):
    def __init__(self, shop_name, shop_type, **kwargs):
        super().__init__(shop_name, shop_type, **kwargs)
        self.batch_size = kwargs.get('batch_size', 5)
        self.collections = None
        self.product_ids = None
        self.order_ids = None

    def get_all_collections(self, **kwargs):
        has_active_session = kwargs.get('has_active_session', False)
        if has_active_session == False:
            shopify.ShopifyResource.activate_session(self.shop_api)
        self.collections = spf.get_collection_map()
        if has_active_session == False:
            shopify.ShopifyResource.clear_session()

    def add_collection(self, name,**kwargs):
        has_active_session = kwargs.get('has_active_session', False)
        if has_active_session == False:
            shopify.ShopifyResource.activate_session(self.shop_api)
        
        if self.collections is None: self.get_all_collections(has_active_session=True)
        collection_id = self.collections.get(name)
        if collection_id is None:
            collection_id, suc = spf.add_collection({'title': name})
            if not suc: logger.debug(collection_id)
            collection_id = collection_id['id']
            self.collections[name] = collection_id
            
        if has_active_session == False:
            shopify.ShopifyResource.clear_session()
        return collection_id

    def add_product_to_shop(self,product_info: dict, **kwargs):
        has_active_session = kwargs.get('has_active_session', False)
        if has_active_session == False:
            shopify.ShopifyResource.activate_session(self.shop_api)
        attr_list = kwargs.get('attr_list', ['size', 'color'])

        is_simple_product = product_info.get('variations') is None
        
        variation_imgs = model_to_spf.product_parser(product_info, 
                     attr_list,
                     kwargs.get('variation_attrs'),
                     parent_id=kwargs.get('parent_id'),
                     )
        msg = None 
        suc = False
        if kwargs.get('parent_id') is None:
            msg, suc = spf.add_product(product_info, variant_imgs=variation_imgs)
        else:
            msg = {'id': kwargs['parent_id'], 'variants': []}
            for vari in product_info['variants']:
                msg_variant, suc = spf.add_variation(msg['id'], vari)
                if suc == True: msg['variants'].append(msg_variant)
            
        if suc == True:
            if kwargs.get('parent_id') is None and product_info.get('category') is not None:
                collection_id = self.add_collection(product_info['category'],
                                                   has_active_session=True)
                if collection_id:
                    spf.add_product_to_collection(msg['id'], collection_id)
            # if kwargs.get('update_inventory'):
            #     for i,vari in enumerate(product_info['variants']):
            #         qty = vari.get('in_stock', product_info.get('in_stock'))
            #         inventory_item_id = msg['variants][i]['inventory_item_id']
            #         if qty:
            #             self.update_shop_product({'inventory_item_id': inventory_item_id, 
            #                                    'in_stock': qty}, 
            #                                   vari['id'],
            #                                   has_active_session=True)    
        
        if has_active_session == False:
            shopify.ShopifyResource.clear_session()

        if suc == True:
            return self._parse_product(msg, is_simple_product=is_simple_product)

        logger.debug(msg)

    
    def add_product_to_shop_bulk(self, products:list,  **kwargs):
        shopify.ShopifyResource.activate_session(self.shop_api)
        for product in products:
            self.add_product_to_shop(product, has_active_session=True, **kwargs)
        shopify.ShopifyResource.clear_session()

    def update_shop_product(self, data:dict, product_id:str, **kwargs ):
        has_active_session = kwargs.get('has_active_session', False)
        if has_active_session == False:
            shopify.ShopifyResource.activate_session(self.shop_api)

        if data.get('inventory_item_id'):
            spf.update_inventory_level(data.get('inventory_item_id'), data, 
                                       variant_id=product_id, **kwargs)
        elif product_id and kwargs.get('parent_id'):
            attr_list = kwargs.get('attr_list', ['size', 'color'])
            # print(data)
            if kwargs.get('formated') is None or kwargs['formated'] == False:
                model_to_spf.product_parser(data, 
                        attr_list,
                        kwargs.get('variation_attrs'),
                        parent_id=kwargs.get('parent_id'),
                        add_new=False
                        )
                spf.update_product(kwargs['parent_id'], product_id, data)
            else:
                spf.update_product(kwargs['parent_id'], product_id, data)
        
        if has_active_session == False:
            shopify.ShopifyResource.clear_session()


    def update_shop_product_batch(self, data:list, **kwargs):
        shopify.ShopifyResource.activate_session(self.shop_api)
        for product in data:
            self.update_shop_product(product, product['product_id'], has_active_session=True, 
                                                parent_id=product['parent_id'], **kwargs)
        shopify.ShopifyResource.clear_session()

    def sync_shop_orders(self,**kwargs):
        shopify.ShopifyResource.activate_session(self.shop_api)
        orders = []
        params = {'status': 'any'}
        if kwargs.get('latest_order_id'): params['since_id'] = kwargs['latest_order_id']
        if kwargs.get('status'): params['status'] = kwargs['status']
        if kwargs.get('fields'): params['fields'] = kwargs['fields']
        res =spf.get_all_orders(**params)
        for item in res:
            orders.append(spf_to_model.parse_order(item, self.field_mapping, **kwargs))

        shopify.ShopifyResource.clear_session()
        return orders

    def update_order_status_at_shop(self, destination_order_id: str, 
                                   status: str,**kwargs):
        has_active_session = kwargs.get('has_active_session', False)
        if has_active_session == False:
            shopify.ShopifyResource.activate_session(self.shop_api)
        
        if status not in ('cancel', 'cancelled'):
            logger.debug(f'status not support: {status}')
        else:
            spf.update_order_status(destination_order_id, 'cancel')

        if has_active_session == False:
            shopify.ShopifyResource.clear_session()
        

    def update_order_at_shop(self, destination_order_id: str, 
                             data, **kwargs):
        # has_active_session = kwargs.get('has_active_session', False)
        # if has_active_session == False:
        #     shopify.ShopifyResource.activate_session(self.shop_api)

        # spf.update_order()

        # if has_active_session == False:
        #     shopify.ShopifyResource.clear_session()
        pass

    def update_order_item_at_shop(self, destination_order_id: str, 
                             items: dict, **kwargs):
        """not supported in shopify (after order has been created)
           todo: graphAPI
        """
        pass
        # has_active_session = kwargs.get('has_active_session', False)
        # if has_active_session == False:
        #     shopify.ShopifyResource.activate_session(self.shop_api)
        
        # model_to_spf.transform_order_item(items)
        # from pprint import pprint
        # pprint(items)
        # spf.update_line_items(destination_order_id, items)

        # if has_active_session == False:
        #     shopify.ShopifyResource.clear_session()

    def get_order_at_shop(self, **kwargs):
        if kwargs.get('destination_order_id') is None:
            logger.debug('missing order id')
            return
        has_active_session = kwargs.get('has_active_session', False)
        if has_active_session == False:
            shopify.ShopifyResource.activate_session(self.shop_api)
        res = spf.get_order_info(kwargs.get('destination_order_id'))
        order = spf_to_model.parse_order(res, self.field_mapping, **kwargs)
        if has_active_session == False:
            shopify.ShopifyResource.clear_session()

        return order

        
    def get_products_at_shop(self,**kwargs):
        """page start from 0"""
        shopify.ShopifyResource.activate_session(self.shop_api)
        if self.product_ids is None:
            self.product_ids = spf.get_all_products(fields='id')
        logger.debug(f"total products {len(self.product_ids)}")
        batch = kwargs.get('batch_size', 5)
        start_i = kwargs.get('page', 0) * batch
        products = []
        for i in range(start_i, min(len(self.product_ids), start_i + batch)):
            products.append(self.get_product_at_shop(
                                 None, parent_id=self.product_ids[i]['id'], 
                                 has_active_session=True, **kwargs))
        shopify.ShopifyResource.clear_session()
        return products
                                    
    def get_product_at_shop(self, product_id: str, include_meta=True, **kwargs):
        has_active_session = kwargs.get('has_active_session', False)
        if has_active_session == False:
            shopify.ShopifyResource.activate_session(self.shop_api)

        product = None
        if kwargs.get('parent_id') is None:
            product = spf.find_variation(product_id, 
                                        include_meta=include_meta)
        else:
            product =spf.get_product_info(kwargs['parent_id'], 
                                        include_meta=include_meta)
        
        if has_active_session == False:
            shopify.ShopifyResource.clear_session()
       
        return spf_to_model.parse_product(product, self.field_mapping)
        
    
    def get_category_taxonomy(self):
        if self.collections is None: 
            self.get_all_collections()
        
        return [{'category': name} for name in self.collections.keys()]
    
    def update_customer_at_shop(self,destination_order_id: str, 
                             data: dict, **kwargs):
        shopify.ShopifyResource.activate_session(self.shop_api)
        model_to_spf.transform_customer(data)
        res, suc = spf.update_customer(destination_order_id, data, **kwargs)
        shopify.ShopifyResource.clear_session()
        if suc == True:
            return res 

        logger.debug(f'update customer failed: {res}')

    def add_tracking(self,destination_order_id: str, 
                            data: dict, **kwargs):
        """ff_info ={"location_id":66061795498,
            "tracking_numbers":["123456789"],
            "tracking_urls":["https://tracking.com/?abc"],
            "tracking_company": 'TBD',
            "notify_customer":False}"""
        shopify.ShopifyResource.activate_session(self.shop_api)
        ff_info = model_to_spf.transform_tracking(data, message=kwargs.get('message', True),
                                                add_new=kwargs.get('add_new', True))
        
        if kwargs.get('location_id') is None:
            #get location_id
            locations = spf.find_location()
            ff_info['location_id'] = locations[0]['id']
        else:
            ff_info['location_id'] = kwargs['location_id']

        _, do_update =spf.update_fulfillment_tracking(destination_order_id, 
                                                           ff_info,**kwargs)
        shopify.ShopifyResource.clear_session()

        return do_update

    def send_message(self, destination_order_id: str, 
                            message: str, **kwargs):
        """not supported by shopify"""
        pass


    def _parse_product(self, p, **kwargs):
        is_simple_product = kwargs.get('is_simple_product', False)
        if is_simple_product:
            data = p['variants'][0]
            data['destination_parent_id'] = str(p['id'])
            return data 
        elif p.get('variants') and len(p['variants']) > 0:
            data = {}
            for vari in p['variants']:
                vari['destination_parent_id'] = str(p['id'])
                data[vari['sku']] = vari 
            return data
        return p



