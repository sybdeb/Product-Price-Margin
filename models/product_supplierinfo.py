# -*- coding: utf-8 -*-

from odoo import models, api


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    def write(self, vals):
        """Trigger herberekening van productprijs als leveranciersprijs wijzigt"""
        result = super(ProductSupplierinfo, self).write(vals)
        
        # Als prijs, voorraad of active wijzigt, update sequences en herbereken prijs
        if any(field in vals for field in ['price', 'supplier_stock', 'active']):
            for supplier in self:
                if supplier.product_tmpl_id:
                    # Update supplier sequences op basis van config regels
                    supplier.product_tmpl_id.update_supplier_sequences()
                    
                    # Herbereken productprijs
                    if supplier.active:
                        supplier.product_tmpl_id._compute_calculated_list_price()
                        if supplier.product_tmpl_id.calculated_list_price:
                            supplier.product_tmpl_id.list_price = supplier.product_tmpl_id.calculated_list_price
        
        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Trigger herberekening bij aanmaken nieuwe supplier"""
        records = super(ProductSupplierinfo, self).create(vals_list)
        
        for supplier in records:
            if supplier.product_tmpl_id:
                # Update sequences
                supplier.product_tmpl_id.update_supplier_sequences()
                
                # Herbereken prijs
                if supplier.price and supplier.active:
                    supplier.product_tmpl_id._compute_calculated_list_price()
                    if supplier.product_tmpl_id.calculated_list_price:
                        supplier.product_tmpl_id.list_price = supplier.product_tmpl_id.calculated_list_price
        
        return records
