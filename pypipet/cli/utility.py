import click

def col2dict(sku, row, default_brand):
    d = {'product': {'variations': {}}, 'destination': {}}
    for k, val in dict(row).items():
        # print(k)
        if val.strip() == '': continue
        table, col = k.split('.')
        if table == 'product':
            d[table][col] = val
        elif table == 'destination':
            if col == 'price': val = float(val)
            if col == 'destination_product_id': val = str(val)
            if col == 'discount': val = float(val)
            if col == 'available': val = not val.lower() == 'false'
            
            d[table][col] = val
        elif table == 'variation':
            if col == 'upc': val = str(val)
            if col == 'in_stock': val = int(val)
            if val in ('True', 'False'):
                val = val == True
            d['product']['variations'][col] = val 
    
    if d['product'].get('brand') is None:
        d['product']['brand'] = default_brand
    if d['product'].get('short_description') is None \
            or d['product'].get('short_description') == '':
        d['product']['short_description']= \
                    d['product']['product_name']

    d['product']['variations'] = [d['product']['variations']]
    d['destination']['sku'] = sku
    return d


def col2dict_update(sku, row):
    d = {'product': {}, 'variation': {}, 'destination': {}}
    for k, val in dict(row).items():
        if val.strip() == '': continue
        table, col = k.split('.')
        if table == 'product':
            if col == 'id': val = int(val)
            d[table][col] = val
        elif table == 'destination':
            if col == 'price': val = float(val)
            if col == 'destination_product_id': val = str(val)
            if col == 'discount': val = float(val)
            if col == 'available': val = not val.lower() == 'false'
            
            d[table][col] = val
        elif table == 'variation':
            if col == 'upc': val = str(val)
            if col == 'in_stock': val = int(val)
            d['variation'][col] = val 
    
    if len(d['destination']) > 0:
        d['destination']['sku'] = sku
    return d

def map_product_sku_for_launch(df):
    res = []
    for i, row in df.iterrows():
        row = dict(row)
        price = None 
        if _has_value(row.get('destination.price'), data_type='float'):
            price =float(row['destination.price'])
        elif _has_value(row.get('price'), data_type='float'):
            price =float(row['price'])
        if price is None:
            click.secho('missing price in row {}'.format(i+1),
                   fg='yellow')
            continue

        sku = None 
        if _has_value(row.get('variation.sku')):
            sku = row['variation.sku']
        elif _has_value(row.get('sku')):
            sku = row['sku']

        if sku is None:
            click.secho('missing sku in row {}'.format(i+1),
                   fg='yellow')
            continue
        res.append({'sku': sku, 'price': price})
    return res

        

def _has_value(d, data_type=None):
    if d is None: return False
    if d.strip() == '': return False
    if data_type == 'float':
        try:
            d = float(d)
        except:
            return False 
    return True