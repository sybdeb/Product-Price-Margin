# -*- coding: utf-8 -*-

from odoo import models, fields, api


class WebshopCatalogDashboard(models.Model):
    _inherit = 'webshop.catalog.dashboard'

    products_without_margin = fields.Integer(
        string='Producten Zonder Marge Config',
        compute='_compute_margin_stats'
    )
    products_with_deviation = fields.Integer(
        string='Producten Met Afwijkende Marge',
        compute='_compute_margin_stats'
    )

    @api.depends('product_ids')
    def _compute_margin_stats(self):
        for dashboard in self:
            published_products = dashboard.product_ids.filtered(lambda p: p.is_published)
            
            dashboard.products_without_margin = len(published_products.filtered(
                lambda p: not p.margin_config_id
            ))
            dashboard.products_with_deviation = len(published_products.filtered(
                lambda p: p.has_margin_deviation
            ))

    def action_view_products_without_margin(self):
        """Open lijst van producten zonder marge configuratie"""
        self.ensure_one()
        published_products = self.product_ids.filtered(lambda p: p.is_published)
        products_without_margin = published_products.filtered(lambda p: not p.margin_config_id)
        
        return {
            'name': 'Producten Zonder Marge Configuratie',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'list,form',
            'domain': [('id', 'in', products_without_margin.ids)],
            'context': {'create': False},
        }

    def action_view_products_with_deviation(self):
        """Open lijst van producten met afwijkende marge"""
        self.ensure_one()
        published_products = self.product_ids.filtered(lambda p: p.is_published)
        products_with_deviation = published_products.filtered(lambda p: p.has_margin_deviation)
        
        return {
            'name': 'Producten Met Afwijkende Marge',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'list,form',
            'domain': [('id', 'in', products_with_deviation.ids)],
            'context': {'create': False},
        }
