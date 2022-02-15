import yaml

def db_yml_config(filename):
    """Return current db configuration in `yml`."""
    # todo validate db setting 
    with open(filename, 'r') as f:
        return yaml.safe_load(f)

def load_mapping(filename):
    with open(filename, 'r') as f:
        return yaml.safe_load(f)


def validate(db_setting):
    if db_setting.get('db_setting') is None:
        return False, 'can not find db_setting'

    if db_setting['db_setting'].get('db_type') is None:
        return False, 'can not find db_type'

    if db_setting['db_setting'].get('db_conn') is None:
        return False, 'can not find db_conn'

    conn = db_setting['db_setting']['db_conn']
    check_attrs = ['host', 'port', 'user', 'password', 'dbname']
    for attr in check_attrs:
        if conn.get(attr) is None:
            return False, f'can not find {attr} in db_conn'

    if db_setting['db_setting'].get('tables') is None:
        return False, 'can not find tables'

    tables = db_setting['db_setting']['tables']

    table_validation = {
        'category': ['category', 'full_path'],
        'product': ['product_name', 'identifier'],
        'front_shop': ['name', 'provider'],
        'variation': ['sku', 'description',  'product_id'],
        'tax': ['name', 'country_code', 'default_rate'],
        'destination': ['destination_product_id', 'price', 'currency',
                    'is_current_price', 'sku', 'front_shop_id', 'available'],
        'inventory': ['sku', 'cost', 'currency', 'supplier_item_id', 'supplier_id'],
        'customer': ['first_name','last_name','phone', 'email', 'address1',
                    'address2', 'country', 'state', 'city', 'postcode', 
                    'is_shipping', 'is_billing'],
        'shop_order': ['destination_order_id', 'front_shop_id', 'status',
                     'billing_customer_id','shipping_customer_id',
                     'payment_type','payment_token', 'refund', 'shipping_cost',
                     'shipping_tax_id', 'order_total','order_at','currency'],
        'order_item': ['shop_order_id', 'destination_id','destination_product_id',
                      'tax_id', 'order_qty', 'ship_qty'],
        'fulfillment': ['provider', 'status', 'dimension', 'weight', 
                      'tracking_id', 'shop_order_id', 'destination_order_id']
    }

    for k, val in table_validation.items():
        if tables.get(k) is None:
            return False, f'missing table {k}'
        
        if tables[k].get('columns') is None:
            return False, f'{k} missing columns'

        cols = [c['name'] for c in tables[k]['columns']]
        for col in val:
            if col not in cols:
                return False, f'{k} missing column {col}'

    return True, None


            