from copy import deepcopy
from math import prod
from pprint import pprint

def add_metafields(attributes: dict, attr_list, option_attrs=None, 
                namespace='variant'):
    # shopify: max two options in option_attrs
    # add more to metafields
    meta = []
    for attr, value in attributes.items():
        if attr not in attr_list: continue
        if option_attrs and attr in option_attrs:
            pass
        else:
            meta.append({
                'key': attr,
                'value': str(value),
                "type": "single_line_text_field",
                'namespace': namespace,
            })
    if len(meta) > 0:
        return meta

def variant_parser(variation, option_attrs=None):
    if variation:
            for j, attr in enumerate(option_attrs):
                if variation.get(attr) is not None:
                    variation[f'option{j+1}'] = variation[attr]

            meta = add_metafields(variation, option_attrs=option_attrs)
            if meta:
                variation['metafields'] = meta
            
            # del variation['attributes']
    if variation.get('images'):
        variation['images'] = transform_imgs(variation['images'])

def product_parser(product, attr_list, option_attrs, add_new=True, **kwargs):
    if product.get('created_at'): del product['created_at']
    if product.get('updated_at'): del product['updated_at']
    if product.get('id'): del product['id']
    if product.get('product_id'): del product['product_id']
    if product.get('short_description'):del product['short_description']
    if product.get('description'):
        product['body_html'] = product['description']
        del product['description']

    if product.get('brand') is not None:
        product['vendor'] = product['brand']

    if kwargs.get('weight_unit'):
        product['weight_unit'] = kwargs['weight_unit']
    if product.get('product_name'):
        product['title'] = product['product_name']

    if add_new and product.get('product_type') is None:
        product['product_type'] = product['category']

    imgs, variation_imgs = _parser_img_mapping(product)
    if imgs and len(imgs) > 0:
        product['images'] = imgs

    variants = product.get('variations')
    if variants is None:
        #if it is simple product
        _clean_null(product)
        variants = [deepcopy(product)]

    exist_options = set()

    for i, vari in enumerate(variants):   
        if vari.get('created_at'): del vari['created_at']
        if vari.get('updated_at'): del vari['updated_at']
        
        if vari.get('body_html'): del vari['body_html']
        if vari.get('id'): del vari['id']
        if vari.get('product_id'): del vari['product_id']
        if vari.get('description'): 
            if product.get('body_html') is None:
                product['body_html'] = vari['description']
            del vari['description']
        if vari.get('upc'):
            vari['barcode'] = vari['upc']
        if vari.get('ean'):
            vari['barcode'] = vari['ean']
        
        if option_attrs:
            for j, attr in enumerate(option_attrs):
                if vari.get(attr) is not None:
                    variants[i][f'option{j+1}'] = vari[attr]
                    exist_options.add(attr)

        meta = add_metafields(vari, attr_list, option_attrs=option_attrs)
        if meta:
            variants[i]['metafields'] = meta

        if add_new:
            variants[i]['inventory_management'] = kwargs.get('inventory_management',
                                                            'shopify')
            variants[i]['fulfillment_service'] = kwargs.get('fulfillment_service',
                                                            'manual')
        if vari.get('discount'):
            assert vari['price']
            vari['compare_at_price'] = vari['price'] 
            vari['price'] = vari['price'] - vari['discount']

        #existing parent
        if kwargs.get('parent_id') is None:
            if vari.get('images'): del vari['images']
        elif vari.get('images'):
            variants[i]['images'] = transform_imgs(vari['images'])

        
    product['variants'] = variants

    if product.get('variations'):
        del product['variations']
    # else:
    #     meta_product = add_metafields(product, attr_list)
    #     if meta_product:
    #         product['metafields'] = meta_product

    
    product['variants'] = variants 

    if add_new and option_attrs:
        product['options'] = []
        for attr in option_attrs:
            if attr in exist_options: 
                product['options'].append({'name': attr})

    
    return variation_imgs

def transform_customer(data):
    if data.get('postcode') is not None:
        data['zip'] = data['postcode']
    if data.get('state') is not None:
        data['state'] = data['province']
    if data.get('email') is not None:
        data['email'] = data['email'].lower()
    if data.get('updated_at') is not None:
        del data['updated_at']
    if data.get('created_at') is not None:
        del data['created_at']

def transform_tracking(data, message=True, add_new=True):
    if data:
        if add_new:
            ff_info = {'message': message}
            if data.get('tracking_id'):
                ff_info['tracking_numbers'] = data['tracking_id'].split(',')
            if data.get('tracking_urls'):
                ff_info['tracking_urls'] = data['tracking_urls'].split(',')
            if data.get('provider'):
                ff_info['tracking_company'] = data['provider']
            return ff_info 
        else:
            ff_info = {}
            if data.get('tracking_id'):
                ff_info['number'] = data['tracking_id']
            if data.get('tracking_urls'):
                ff_info['url'] = data['tracking_urls']
            if data.get('provider'):
                ff_info['company'] = data['provider']
            return ff_info    

def transform_order_item(items:dict):
    for variant_id, value in items.items():
        if value.get('destination_product_id'):
            items[variant_id]['variant_id'] = value['destination_product_id']
            del items[variant_id]['destination_product_id']
        if value.get('destination_parent_id'):
            items[variant_id]['product_id'] = value['destination_parent_id']
            del items[variant_id]['destination_parent_id']
        if value.get('sku'):
            items[variant_id]['sku'] = value['sku']
        
        if value.get('order_qty'):
            items[variant_id]['quantity'] = value['order_qty']
            del items[variant_id]['order_qty']
        elif value.get('qty'):
            items[variant_id]['quantity'] = value['qty']
            del items[variant_id]['qty']

    

def _clean_null(data: dict):
    keys = data.keys()
    deleted_keys = []
    for k  in keys:
        if data[k] is None:
            deleted_keys.append(k)

    for k in deleted_keys:
        del data[k]

def transform_imgs(img_str, sep=','):
    return [{'src': img} 
           for img in img_str.split(sep)]

def _parser_img_mapping(product):
    imgs = []
    variation_imgs = {}
    if product.get('variations'):
        for vari in product['variations']:
            if vari.get('images'):
                variation_imgs[vari['sku']] = len(imgs)
                imgs += transform_imgs(vari['images'])
    elif product.get('images'):
        imgs += transform_imgs(product['images'])
    return imgs, variation_imgs