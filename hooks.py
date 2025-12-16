# -*- coding: utf-8 -*-

from odoo import api, fields, SUPERUSER_ID


def post_init_hook(env):
    """Add public_categ_id field if website_sale is installed"""
    if 'product.public.category' in env.registry:
        # Dynamically add the field
        ProductMarginConfig = env['product.margin.config']
        if 'public_categ_id' not in ProductMarginConfig._fields:
            ProductMarginConfig._add_field('public_categ_id', fields.Many2one(
                'product.public.category',
                string='Webshop Categorie',
                ondelete='cascade',
            ))
            ProductMarginConfig._setup_fields()
