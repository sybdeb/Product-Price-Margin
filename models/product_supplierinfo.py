# -*- coding: utf-8 -*-

from odoo import models, api


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    def write(self, vals):
        """Trigger herberekening van productprijs als leveranciersprijs wijzigt"""
        result = super(ProductSupplierinfo, self).write(vals)
        
        # Als de prijs wijzigt, trigger herberekening van het product
        if 'price' in vals:
            for supplier in self:
                if supplier.active and supplier.product_tmpl_id:
                    # Forceer herberekening door computed fields te triggeren
                    supplier.product_tmpl_id._compute_calculated_list_price()
                    # Als er een prijs is, pas die automatisch toe
                    if supplier.product_tmpl_id.calculated_list_price:
                        supplier.product_tmpl_id.list_price = supplier.product_tmpl_id.calculated_list_price
        
        # Als leverancier wordt gearchiveerd, herbereken voorkeur leverancier
        if 'active' in vals:
            for supplier in self:
                if supplier.product_tmpl_id:
                    supplier.product_tmpl_id._compute_preferred_supplier()
                    # Check of product gearchiveerd moet worden
                    if supplier.product_tmpl_id.seller_ids and all(not s.active for s in supplier.product_tmpl_id.seller_ids):
                        supplier.product_tmpl_id.active = False
        
        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Trigger herberekening bij aanmaken nieuwe supplier"""
        records = super(ProductSupplierinfo, self).create(vals_list)
        
        for supplier in records:
            if supplier.product_tmpl_id and supplier.price:
                supplier.product_tmpl_id._compute_calculated_list_price()
                if supplier.product_tmpl_id.calculated_list_price:
                    supplier.product_tmpl_id.list_price = supplier.product_tmpl_id.calculated_list_price
        
        return records
