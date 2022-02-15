# from pypipet.core.sql.model2query import *
# from pypipet.core.sql.query import * 


# def add_supplier_invoice(ctx, session, invoice: dict):
#     if invoice.get('sku') is None:
#         inv_data =  query_select(
#             ctx.get_table_objects().get('inventory'), 
#             session, 
#             filters={'supplier_id': invoice['supplier_id'],
#                     'supplier_item_id': invoice['supplier_item_id']})
#         if len(inv_data) > 0:
#             invoice['sku'] = inv_data[0].sku
        

#     unique_keys = ctx.get_model_keys('supplier_invoice')
#     add_if_not_exist(invoice, 
#                     ctx.get_table_objects().get('supplier_invoice'), 
#                         unique_keys,
#                         session) 
#     return True
