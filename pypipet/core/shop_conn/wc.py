
import logging, time, re
logger = logging.getLogger('__default__')

_MAX_RETRY =3

"""
note: wc can not search precisely with name
"""

def request_handler(func):
    def wrapper(*args, **kwargs):
        try:
            res = func(*args, **kwargs)
            if res and res.status_code in [200, 201]:
                return res.json()
            if res:
                logger.debug(res.text)
            return None
        except  KeyError as e:
            logger.debug('requst error')
            logger.debug(e)
    return wrapper

def request_handler_retry(func):
    def wrapper(*args, **kwargs):
        for i in range(_MAX_RETRY):
            try:
                res = func(*args, **kwargs)
                if res.status_code in [200, 201]:
                    return res.json()
                logger.debug(res.text)
            except  KeyError as e:
                logger.debug('requst error')
                logger.debug(e)
        return None
    return wrapper

# def validate_by_key(key):
#     def decorator(func):
#         def wrapper(*args, **kwargs):
#             try:
#                 res = func(*args, **kwargs)
#                 if res and kwargs.get(key):
#                     for r in res:
#                         if r.get(key) == kwargs.get(key):
#                             return r 
#                 return None

#             except  KeyError as e:
#                 logger.debug('validate error')
#                 logger.debug(e)
#         return wrapper
#     return decorator


#
#------function of handling product-------------
#
# @request_handler
def delete_prouct_by_id(wcapi, product_id, variation_id):
    res = wcapi.delete(f'products/{product_id}/variations/{variation_id}')
    print(res.json())

@request_handler
def search_product_by_sku(wcapi, sku:str):
    return wcapi.get('products', params={'sku': sku})

def get_product_by_sku(wcapi, sku:str):
    res = search_product_by_sku(wcapi, sku)
    for p in res:
        if p['sku'] == sku:
            return p

# @request_handler
def add_product(wcapi, product_info):
    res =  wcapi.post('products', data=product_info)
    if res is None: return 
    if res.status_code in [200, 201]:
        return res.json()
    
    if res and res.json().get('code'):
        error_code = res.json()['code']
        if 'sku' in error_code and 'duplicate' in error_code:
            #update product
            exist_product = get_product_by_sku(wcapi, product_info['sku'])
            if exist_product is not None:
                res =  update_product(
                            wcapi,
                            str(exist_product['id']) ,
                            product_info, 
                            )
                if res and res.status_code in [200, 201]:
                    return res.json()

    logger.debug(res.text)

# @request_handler
def add_product_variations(wcapi, product_info, parent_id=None):
    if parent_id is None:
        res = wcapi.post('products', data=product_info['parent']) 
        if res is None: return 
        if res.status_code not in [200, 201]: 
            logger.debug(res.text)
            return 
        parent_id = res.json()['id']
    else:
        parent_exist = wcapi.get(f'products/{parent_id}')
        if parent_exist.status_code not in (201, 200):
            return 

        #if previously added as imple product
        if product_info['parent'].get('parent_note') == 'INCORRECT_TYPE':
            product_info['parent']['sku'] = f"--{parent_exist.json()['sku']}--"
            wcapi.put(f'products/{parent_id}', data=product_info['parent']) 
        else:
            parent_update = _merge_parent_attrs(product_info['variations'], 
                                            parent_exist.json()['attributes'])
            wcapi.put(f'products/{parent_id}', data={'attributes': parent_update}) 

    if parent_id is not None:
        logger.debug(f'parent_id {parent_id}')
        for i, vari in enumerate(product_info['variations']):
            # note: this is not in woocomerce documents
            # print('sku---', vari['sku'])
            product_info['variations'][i]['product_id'] = parent_id
        
        batch_data = {'create': product_info['variations']}
        res = wcapi.post(f'products/{parent_id}/variations/batch', data=batch_data)
        
        if res is not None and res.status_code in [200, 201]: 
           return  _parse_variation_response(res.json()['create'], parent_id)
        else:
            logger.debug(res.status_code)
            logger.debug(res.json())

def _merge_parent_attrs(variations, prev_attrs):
    addtional_attrs = {}
    for vari in variations:
        for attr in vari['attributes']:
            if addtional_attrs.get(attr['id']) is None:
                addtional_attrs[attr['id']] = []
            addtional_attrs[attr['id']].append(attr['option'])

    for i, attr in enumerate(prev_attrs):
        if addtional_attrs.get(attr['id']) is not None:
            prev_attrs[i]['options']+= addtional_attrs[attr['id']]

    return prev_attrs

def _parse_variation_response(vari_list: list, parent_id):
    res = {}
    for i, vari in enumerate(vari_list):
        if vari.get('sku') is None: 
            logger.debug(f'wc bulk add failed {vari}')
            continue
        res[vari['sku']] = {
                'destination_product_id': vari['id'],
                'destination_parent_id': parent_id,
                }
    return res

@request_handler
def get_product_by_id(wcapi, pid:int):
    return wcapi.get(f'products/{pid}')

@request_handler
def list_products(wcapi,  params: dict=None):
    """start from page 1
       by default woocommerce order orders by order_id DESC
    """
    if params is None: params ={}
    params.update({
        'orderby': 'id',
        'order': 'asc'
    })
    return wcapi.get('products', params=params)


@request_handler
def update_product(wcapi, pid:str, data:dict):
    if data.get('regular_price') and type(data['regular_price']) is not str:
        data['regular_price'] = str(round(data['regular_price'], 2))
    if data.get('sale_price') and type(data['sale_price']) is not str:
        data['sale_price'] = str(round(data['sale_price'], 2))
    # print(data, pid)
    return wcapi.put(f'products/{pid}', data=data) 

@request_handler_retry
def update_product_batch(wcapi, action:str, data:list):
    batch_data = {action: data}
    return wcapi.post(f'products/batch', data=batch_data) 

@request_handler
def add_variation(wcapi, product_id, variation_info):
    wcapi.post(f'products/{product_id}/variations', data=variation_info)

@request_handler
def list_variations(wcapi, product_id, params: dict ={}):
    params.update({
        'orderby': 'id',
        'order': 'asc'
    })
    return wcapi.get(f'products/{product_id}/variations', params=params)

@request_handler
def get_variation(wcapi, product_id, variation_id):
    return wcapi.get(f'products/{product_id}/variations/{variation_id}')

@request_handler
def update_variation(wcapi, product_id, variation_id, data):
    if data.get('regular_price') and type(data['regular_price']) is not str:
        data['regular_price'] = str(round(data['regular_price'], 2))
    if data.get('sale_price') and type(data['sale_price']) is not str:
        data['sale_price'] = str(round(data['sale_price'], 2))
    
    variant = get_variation(wcapi, product_id, variation_id)
    
    if data.get('attributes') is None or len(data['attributes']) == 0:
        data['attributes'] = variant['attributes']
    else:
        data['attributes'] += variant['attributes']
    return wcapi.put(f'products/{product_id}/variations/{variation_id}', data)

# @request_handler
# def update_variations_batch(wcapi, product_id,  action:str, data:list):
#     batch_data = {action: data}
#     return wcapi.post(f'products/{product_id}/variations/batch', data=batch_data)

@request_handler
def list_categories(wcapi, page:int, per_page:int =10, params: dict=None):
    """start from page 1
       by default woocommerce order orders by order_id DESC
    """
    if params is None: params ={}
    params.update({
        'page': page,
        'per_page': per_page,
        'orderby': 'id',
        'order': 'asc'
    })
    return wcapi.get('products/categories', params=params)



#
#------function of handling orders-------------
#



@request_handler
def list_orders(wcapi, page:int, per_page:int =10):
    return wcapi.get('orders', params={'page': page,
                                         'per_page': per_page})

@request_handler
def get_order_by_id(wcapi, oid):
    return wcapi.get(f'orders/{oid}')

def get_new_orders(wcapi, start_from_order:str=None, 
                     page_start:int = 1, per_page:int =10):
    """
    sync new orders from wp 
    start_from_order: latest inserted order id 
    page_start: fetch from page number
    """
    orders = []
    page = page_start
    while True:
        logger.debug(f'fetching order page {page}')
        batch = list_orders(wcapi, page, per_page=per_page)
        if batch is None: return None
        if len(batch) == 0: break
        for order in batch:
            if start_from_order is not None and \
            str(order['id']) == start_from_order.strip():
                return orders
            orders.insert(0,order)
        page += 1 

    return orders

@request_handler
def send_note(wcapi, order_id:str, data:dict):
    return wcapi.post(f'orders/{order_id}/notes', data=data)
    

def send_wc_message(wcapi, order_id: str, template: str):
    res = send_note(wcapi, order_id, data={
        'customer_note': True,
        'note': template
    })
    return res

@request_handler
def update_order(wcapi, order_id, data):
    return wcapi.put(f'orders/{order_id}', data)

# @request_handler
# def update_customer(wcapi, customer_id, data):
#     print(data, customer_id)
#     return wcapi.put(f'customers/{customer_id}', data)

#
#------function of transforming product attributes-------------
#

def transform_imgs(image_str):
    try:
        images = image_str.split(',')
        return [{'src': img.strip(), "position": i}
                for i, img in enumerate(images)]
    except:
        return []

def transform_categories(wcapi, full_path, sep='>'):
    cats = full_path.split('>')
    parent_id = None
    categories = []
    for c in cats:
        new_cat = transform_category(wcapi, c, parent_id=parent_id)
        assert new_cat is not None
        categories.append(new_cat)
        # parent = new_cat
    return categories

def transform_category(wcapi, category, parent_id=None):
    category = get_category(wcapi, category.strip(), parent_id=parent_id)
    if category is None:
        return None 
    return {'id': category['id']}


def get_category(wcapi, name, parent_id=None):
    category = search_category(wcapi, name)
    if category is not None:
        return category

    data  = {'name': name}
    if parent_id:
        data['parent'] = parent_id
    return add_category(wcapi, data)

@request_handler
def add_category(wcapi, data):
    return  wcapi.post('products/categories', data=data)

def search_category(wcapi, name):
    name_slug = re.sub('[^a-zA-Z0-9_]+', '-', name.replace('\'', ''))
    # print(name, name_slug)
    res = wcapi.get('products/categories', params={'search': name_slug})
    if res.status_code in [200, 201]:
        for cat in res.json():
            if cat['slug'] == name_slug.lower():
                return cat
    return None

@request_handler
def add_brand(wcapi, name):
    return wcapi.post('products/brands', data={'name': name})
    

def get_brand(wcapi, name):
    name_slug = re.sub('[^a-zA-Z0-9]+', '-', name.lower())
    res = wcapi.get('products/brands', params={'search': name_slug})
    if res.status_code in [200, 201]:
        for item in res.json():
            if item['slug'] == name_slug:
                return item
        return add_brand(wcapi, name)
    else:
        logger.debug(res.text)
        return None 

def transform_brand(wcapi, name):
    if name:
        brand = get_brand(wcapi, name)
        if brand is not None:
            return [brand['id']]

# def get_tags(wcapi, names):
#     tags = []
#     for name in names:
#         t = getTag(wcapi, name.strip().lower())
#         # assert t is not None
#         if t is None: continue
#         tags.append({'id': t})
#     return tags

@request_handler
def add_attr(wcapi, name):
    return wcapi.post("products/attributes", data={
        'name': name
    })


def get_attr(wcapi, name):
    res = wcapi.get('products/attributes', params={'search': name})
    if res.status_code in [200, 201]:
        for item in res.json():
            if item['name'].lower() == name.lower():
                return item
        return add_attr(wcapi, name)
    logger.debug(res.text)
    return None 

def transform_attrs(wcapi, attrs_list, product_info):
    attrs = []
    for attr_name in attrs_list:
        if product_info.get(attr_name) is None \
                   or str(product_info[attr_name]).strip() == "": 
            continue
        attr = get_attr(wcapi, attr_name)
        if attr is  None: continue

        attrs.append({
            'id' : attr['id'], 
            # 'position' : 0,
            'visible' : True,
            'options' : [
                str(product_info[attr_name])]
        })

       
    return attrs



def transform_attrs_variations(wcapi, attrs_list, variations, 
                                        variation_attrs, addtional_attrs={}):
    parent_attrs = {}
    for attr_name in attrs_list:
        attr = get_attr(wcapi, attr_name)
        if attr is  None: continue
            
        if parent_attrs.get(attr_name) is None:
            parent_attrs[attr_name] = {
                'id' : attr['id'], 
                'visible' : True,
                'options' : []
            }


    for vari in variations:
        vari['sub_title'] = ''
        attrs = []
        for attr_name in attrs_list:
            if vari.get(attr_name) is None \
                    or str(vari[attr_name]).strip() == "": 
                continue

            if parent_attrs.get(attr_name) is None:
                continue
            
            if attr_name in variation_attrs:
                attrs.append({
                    'id' : parent_attrs[attr_name]['id'], 
                    # 'position' : 0,
                    'option' : str(vari[attr_name])
                })
                vari['sub_title'] += vari[attr_name] + ' '
                parent_attrs[attr_name]['variation'] = True
         
            if len(parent_attrs[attr_name] ['options']) == 0 \
            or parent_attrs[attr_name].get('variation') == True \
            or attr_name.lower() in ('upc', 'mpn', 'din'):
                parent_attrs[attr_name]['options'].append(str(vari[attr_name]))
        vari['attributes'] = attrs
    
    parent_attrs.update(addtional_attrs)
    empty_attrs = []
    for k, val in parent_attrs.items():
        if val and( type(val) is str or val.get('id') is None):
            attr = get_attr(wcapi, k)
            if attr is  None: continue
                
            parent_attrs[k] = {
                    'id' : attr['id'], 
                    'visible' : True,
                    'options' : [str(val)]
                }   
        elif val and len(val['options']) == 0:
            empty_attrs.append(k)

    for attr in empty_attrs:
        del parent_attrs[attr]
       
    return list(parent_attrs.values())

# def transform_dimension(wcapi, product_info):
#     product_info['dimensions'] =  {
#         'length': str(product_info['length']),
#         'width': str(product_info['width']),
#         'height': str(product_info['height'])
#     }