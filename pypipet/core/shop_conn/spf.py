from dataclasses import fields
from email import message
from turtle import up
import shopify
from shopify.resources import fulfillment_service
from pyactiveresource.activeresource import ActiveResource
from shopify.resources.custom_collection import CustomCollection
import logging
logger = logging.getLogger('__default__')

_ignore_status = ('cancelled', 'error', 'failure')

def add_request_handler(func):
    def wrapper(*args, **kwargs):
        try:
            res, suc = func(*args, **kwargs)
            if suc:
                return res.attributes, suc
            
            return res.errors.errors, suc
        except Exception  as e:
            logger.debug('requst error')
            logger.debug(e)
            return None, None
    return wrapper

def request_handler(func):
    def wrapper(*args, **kwargs):
        try:
            res = func(*args, **kwargs)
            if res is None:
                return 
            if isinstance(res, list):
                return [r.attributes for r in res]
            elif isinstance(res,ActiveResource):
                return res.attributes
            return res
            
        except Exception  as e:
            logger.debug('requst error')
            logger.debug(e)
            return 
    return wrapper

def update_request_handler(func):
    def wrapper(*args, **kwargs):
        try:
            res = func(*args, **kwargs)
            return res
            
        except Exception  as e:
            logger.debug('requst error')
            logger.debug(e)
            return 
    return wrapper


@add_request_handler
def _add_product(data: dict, status='active', publish_scope='web', **kwargs):
    data.update({
        'status': status,
        'publish_scope': publish_scope
    })
    if kwargs.get('template'): 
        data['template_suffix'] = kwargs['template']

    p = shopify.Product(attributes=data)
    suc = p.save()

    return p, suc

def add_product(data: dict, status='active', publish_scope='web', **kwargs):
    p, suc = _add_product(data, status, publish_scope, **kwargs)
    #unfold variants
    if p and p.get('variants'):
        for i, vari in enumerate(p['variants']):
            if isinstance(vari, ActiveResource):
                if kwargs.get('variant_imgs') and \
                kwargs['variant_imgs'].get(vari.sku) is not None:
                    vari.image_id = p['images'][kwargs['variant_imgs'][vari.sku]].id
                    vari.save()
                p['variants'][i] = vari.attributes
    return p, suc

@request_handler
def add_product_to_collection(product_id, collection_id):
    res = shopify.Collect.create({"collection_id": collection_id, 
                         "product_id": product_id})
    return res
 
def add_products_bulk():
    pass

@request_handler
def find_product(product_id=None):
    if product_id is not None:
        return shopify.Product.find(product_id)
    else:
        return shopify.Product.find()

def get_product_info(product_id, **kwargs):
    info = find_product(product_id)
    if info:
        if  info.get('variants'):
            for i, vari in enumerate(info['variants']):
                info['variants'][i] = vari.attributes
                if kwargs.get('include_meta') == True:
                    info['variants'][i]['meta'] = find_metafield(
                    mId=None, resource={
                        'resource_id': vari.id,
                        'resource': f'products/{product_id}/variants'
                    })
        if  info.get('images'):
            for i, img in enumerate(info['images']):
                info['images'][i] = img.attributes
        if  info.get('options'):
            for i, option in enumerate(info['options']):
                info['options'][i] = option.attributes
        if  info.get('image'):
            info['image'] = info['image'].attributes
        if kwargs.get('include_meta') == True:
            # resource ={
            #     'resource_id': 42331660189866,
            #     'resource': 'products/7146500587690/variants'
            # }
            info['meta'] = find_metafield(mId=None, resource={
                    'resource_id': product_id,
                    'resource': 'products'
            })
        return info
    
@request_handler   
def get_products(**kwargs):
    return shopify.Product.find(**kwargs)

def get_all_products(**kwargs):
    products = get_all_items(shopify.Product,  **kwargs)
    return sorted(products, key=lambda d: d['id'])




def get_next_page(obj: ActiveResource=None, first_page=False, 
                      next_url=None, **kwargs):
    if next_url:
        return obj.find(from_=next_url, **kwargs)
    if obj and first_page:
        return obj.find(**kwargs)
    if obj and obj.has_next_page():
        return obj.next_page(**kwargs)

@update_request_handler
def update_product(product_id, variant_id, data):
    p = shopify.Product.find(product_id) 
    product_updates = {}
    from pprint import pprint 
    pprint(data)
    for k, value in data.items():
        if k == 'images' and isinstance(value, list):
            product_updates[k] = p.images + value 
        elif k == 'variants':
            for variant_update in value:
                update_variant(variant_id, variant_update)
        elif k == 'options':
            product_updates[k] = p.options + value 
        elif k == 'destination':
            update_variant(variant_id, value)
        elif k in ('price', 'sku', 'qty', 'in_stock', 
                 'discount', 'compare_at_price', 'available'):
            pass
        elif not (isinstance(value, list) or isinstance(value, dict)):
            product_updates[k] = value
    if len(product_updates) > 0:
        p._update(product_updates)
        p.save()
    return p

def update_products_bulk():
    pass 

@add_request_handler
def add_variation(product_id, data: dict):
    #add image to product
    variant_img_id = None
    if data.get('images'):
        for img in data['images']:
            # print(img)
            new_img, suc = add_image(product_id, img)
            # print(new_img)
            if suc and variant_img_id is None:
                variant_img_id = new_img['id']

    data.update({'product_id': product_id,
                 'image_id': variant_img_id}) 
    variant = shopify.Variant(attributes=data)
    suc = variant.save()
    return variant, suc

@update_request_handler
def update_variant(variant_id, data, **kwargs):
    variant = shopify.Variant.find(variant_id, **kwargs)
    if data.get('available') is not None:
        if data['available'] == False:
            #set qty to 0
            update_inventory_level(variant.inventory_item_id, 
                                            {'in_stock': 0})
            return 
        #update inventory
        update_inventory_level(variant.inventory_item_id, 
                                        {'in_stock': data['in_stock']})
    variant._update(data)
    variant.save()
    return variant

@request_handler
def find_variation(variant_id=None, **kwargs):
    if variant_id is not None:
        return shopify.Variant.find(variant_id, **kwargs)
    else:
        return shopify.Variant.find(**kwargs)

@request_handler
def find_inventory_item(inv_item_id):
    return shopify.InventoryItem.find(inv_item_id)

@request_handler
def find_inventory_level(inv_item_id):
    return shopify.InventoryLevel.find(
        inventory_item_ids=inv_item_id)

@update_request_handler
def update_inventory_level(inv_item_id, data, **kwargs):
    qty = data.get('in_stock')
    if qty is None: qty = data.get('qty')
    if qty is None: 
        logger.debug('invalid quantity')
        return 

    #update variant-inventory_management,fulfillment_service
    if kwargs.get('set_inventory_management') == True \
    and kwargs.get('variant_id'):
        variant = shopify.Variant.find(kwargs['variant_id'])
        inv_item_id = variant.inventory_item_id
        variant._update({
            'inventory_management': kwargs.get('inventory_management','shopify'),
            'fulfillment_service': kwargs.get('fulfillment_service','manual')
        })
        variant.save()

    if inv_item_id is None and kwargs.get('variant_id'):
        variant = shopify.Variant.find(kwargs['variant_id'])
        inv_item_id = variant.inventory_item_id

    items = shopify.InventoryLevel.find(
        inventory_item_ids=inv_item_id)
    
    if items:
        for item in items:
            item.set(item.location_id, inv_item_id, 
                qty, **kwargs)
            
        return items

def get_inventory(inv_item_id):
    inv_item =  find_inventory_item(inv_item_id)
    if inv_item:
        inv_level = find_inventory_level(inv_item_id)
        if inv_level:
            inv_item.update(inv_level)
        return inv_item

# @update_request_handler
# def update_inventory(inv_item_id, data,**kwargs):
#     inv_item = shopify.InventoryItem.find(inv_item_id)
#     inv_item._update(data)
#     inv_item.save()

#     update_inventory_level(inv_item_id, data, **kwargs)



@request_handler
def find_location(location_id=None):
    if location_id is not None:
        return shopify.Location.find(location_id)
    else:
        return shopify.Location.find()

def add_order():
    pass 

def add_orders_bulk():
    pass

def get_all_orders(**kwargs):
    print(kwargs)
    orders = get_all_items(shopify.Order,  **kwargs)
    orders = sorted(orders, key=lambda d: d['id'])
    return [extract_order_info(order) for order in orders ]

@request_handler
def find_order(order_id):
    return shopify.Order.find(order_id) 

def _extract_order_tax(lines):
    for i, item in enumerate(lines):
        lines[i] = item.attributes
        if lines[i].get('tax_lines'):
            lines[i]['tax_lines'] = [t.attributes \
                  for t in lines[i]['tax_lines']]


def extract_order_info(order_info):
    if order_info.get('billing_address') is not None:
        order_info['billing_address'] = order_info['billing_address'].attributes
    if order_info.get('client_details') is not None:
        order_info['client_details'] = order_info['client_details'].attributes
    if order_info.get('customer') is not None:
        order_info['customer'] = order_info['customer'].attributes
    if order_info.get('shipping_address') is not None:
        order_info['shipping_address'] = order_info['shipping_address'].attributes

    if order_info.get('line_items') is not None:
        _extract_order_tax(order_info['line_items'])
    if order_info.get('shipping_lines') is not None:
        _extract_order_tax(order_info['shipping_lines'])

    if order_info.get('fulfillments') is not None:
        for i, ff in enumerate(order_info['fulfillments']):
            order_info['fulfillments'][i] = ff.attributes

    if order_info.get('refunds') is not None:
        for i, refund in enumerate(order_info['refunds']):
            refund_info = refund.attributes
            refund_info['amount'] = 0
            if refund_info.get('transactions'):
                for trans in refund_info['transactions']:
                    refund_info['amount'] += float(trans.amount)
            order_info['refunds'][i] = refund_info

    return order_info

def get_order_info(order_id):
    order = find_order(order_id) 
    return extract_order_info(order)

@update_request_handler
def update_order(order_id, order_data):
    order = shopify.Order.find(order_id)
    order._update(update_order)
    suc = order.save()
    return order, suc

@update_request_handler
def update_line_items(order_id, items, **kwargs):
    """not supported in shopify (after order has been created)"""
    pass
    # order = shopify.Order.find(order_id, fields='line_items')
    # line_items = order.line_items
    # for item in line_items:
    #     if items.get(str(item.variant_id)) is not None:
    #         from pprint import pprint
    #         print('-------------line_item',item.quantity)
    #         # item._update({'quantity': 1})
    #         item.quantity = 1
    #         suc = item.save()
    #         logger.debug(f'update line item {item.variant_id} in order {order_id}: {suc}')

@update_request_handler
def update_order_status(order_id, status):
    order = shopify.Order.find(order_id)
    did_update = False
    if order:
        if status == 'close':
            order.close()
            did_update = True
        elif status == 'open':
            order.open()   
            did_update = True 
        elif status == 'cancel':
            order.cancel()  
            did_update = True
    return did_update

@add_request_handler
def update_customer(order_id, customer_data, customer_id=None, **kwargs):
    """"shopify can not update billing address with api"""
    order = shopify.Order.find(order_id, fields='id,customer')
    if customer_id is None:
        customer_id = order.customer.id
    
    update_order = {}
    customer_update = {}
    if kwargs.get('is_billing'):
        # update_order['billing_address'] = customer_data
        if customer_data.get('email'): 
            update_order['email'] = customer_data['email']
            customer_update['email'] = customer_data['email']
        if customer_data.get('phone'): 
            update_order['phone'] = customer_data['phone']
            customer_update['phone'] = customer_data['phone']
    if kwargs.get('is_shipping'):
        update_order['shipping_address'] = customer_data
   
    if len(update_order) > 0:
        order._update(update_order)
        suc = order.save()
    
    if len(customer_update) > 0:
        customer = shopify.Customer.find(customer_id)
        if customer_data.get('address1') and customer_data.get('zip') \
        and customer_data.get('province') and customer_data.get('country'):
            
            customer_update['addresses'] = customer.addresses + [customer_data]
            
        customer._update(customer_update)
        suc = customer.save()

    return order, suc
    

@request_handler
def find_fulfillment(include_cancelled=False, **kwargs):
    ffs = shopify.Fulfillment.find(**kwargs)
    if ffs and not include_cancelled:
        filtered_ffs = []
        for ff in ffs:
            if ff.status != 'cancelled':
                filtered_ffs.append(ff)
        return filtered_ffs 

    return ffs



def _order_has_ff(ffs):
    if ffs is None or len(ffs) == 0:
        return False 
    for ff in ffs:
        if ff.status in _ignore_status:
            return False 

    return True
    

@update_request_handler
def update_fulfillment_tracking(order_id, ff_data, add_new=True, message=True, 
                                      ff_id=None, **kwargs):
    exists = shopify.Fulfillment.find(order_id=order_id)
    if add_new and not _order_has_ff(exists):
        ff = shopify.Fulfillment(
            attributes=ff_data, prefix_options={'order_id': order_id}
        )
        ff.save()
        return ff, True
    elif not add_new and exists and len(exists) > 0:
        did_update = False
        for ff in exists:
            if ff_id is None or ff_id == ff.id:
                if ff.status in _ignore_status:
                    continue
                suc = ff.update_tracking(ff_data, message)
                did_update = True
        return exists, did_update
    else:
        return exists, False

def update_shipment_status(order_id, status_data,ff_id=None):
    exists = shopify.Fulfillment.find(order_id=order_id)
    did_update = False
    for ff in exists:
        if ff.status in _ignore_status:
            continue
        if ff_id is None or ff_id == ff.id:
            ff_event = shopify.FulfillmentEvent(
                attributes=status_data, 
                prefix_options={
                    'order_id': order_id,
                    'fulfillment_id': ff.id
                })
            suc = ff_event.save()
            did_update = suc
            
    return did_update


@update_request_handler
def cancel_fulfillment_status(order_id,  ff_id=None):
    exists = shopify.Fulfillment.find(order_id=order_id)
    if exists and len(exists)>0:
        did_update = False
        for ff in exists:
            if ff_id is None or ff_id == ff.id:
                ff.cancel()
                did_update = True
        return exists, did_update

    return None, False

def send_messages():
    pass

@add_request_handler
def add_collection(data):
    c = shopify.CustomCollection(attributes=data)
    suc = c.save()
    return c, suc

@update_request_handler
def udpate_collection(collection_id, data):
    c = shopify.CustomCollection.find(collection_id)
    c._update(data)
    c.save()
    return c

def get_collection_map():
    collections = get_all_items(shopify.CustomCollection, 
                  fields='id,title')
    cmap = {}
    for c in collections:
        cmap[c['title']] = c['id']
    return cmap

@request_handler
def find_collections(**kwargs):
    return shopify.CustomCollection.find(**kwargs)

def get_all_items(item:ActiveResource, **kwargs):
    items = []
    page = get_next_page(item, first_page=True, **kwargs)
    if page:
        items += [r.attributes for r in page]
    # print(page.next_page_url)
    while page and page.next_page_url:
        page = get_next_page(next_url= page.next_page_url)
        if page:
            items += [r.attributes for r in page]
    return items
    


@add_request_handler
def add_image(product_id, data):
    data['product_id'] = product_id
    img = shopify.Image(attributes=data)
    suc = img.save()
    return img, suc


def get_images():
    pass 

@request_handler
def find_metafield(mId=None, resource=None):
    if mId is None:
        m = shopify.Metafield()
        if resource is not None:
            return m.find(**resource)
        else:
            return m.find()
        
    else:
        return shopify.Metafield.find(mId, prefix_options=resource)

@add_request_handler
def add_metafield(data, resource=None):
    m = shopify.Metafield(attributes=data, prefix_options=resource)
    suc = m.save()
    return m, suc

