# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductMarginConfig(models.Model):
    _name = 'product.margin.config'
    _description = 'Product Margin Configuration'
    _order = 'sequence, name'

    def _get_config_type_selection(self):
        """Dynamisch de config_type opties bepalen op basis van geïnstalleerde modules"""
        options = [('brand', 'Per Merk')]
        if 'product.public.category' in self.env:
            options.append(('category', 'Per Webshop Categorie'))
        return options

    name = fields.Char(string='Naam', required=True)
    sequence = fields.Integer(string='Volgorde', default=10)
    active = fields.Boolean(string='Actief', default=True)
    
    # Type configuratie
    config_type = fields.Selection(
        selection='_get_config_type_selection',
        string='Type', 
        required=True, 
        default='brand'
    )
    
    # Relaties
    brand_id = fields.Many2one(
        'product.brand',
        string='Product Merk',
        ondelete='cascade',
    )
    # Note: public_categ_id is added via product_public_category.py when website_sale is installed
    
    # Marge configuratie
    margin_percentage = fields.Float(
        string='Marge %',
        required=True,
        help='Marge percentage dat wordt toegepast op de inkoopprijs'
    )
    
    # Computed velden voor display
    brand_name = fields.Char(related='brand_id.name', string='Merk', store=True)
    category_name = fields.Char(string='Categorie', compute='_compute_category_name', store=True)

    @api.depends('public_categ_id')
    def _compute_category_name(self):
        """Compute category name if field exists"""
        for record in self:
            if hasattr(record, 'public_categ_id') and record.public_categ_id:
                record.category_name = record.public_categ_id.name
            else:
                record.category_name = False

    @api.constrains('config_type', 'brand_id')
    def _check_config_consistency(self):
        """Controleer dat de juiste velden zijn ingevuld per type"""
        for record in self:
            if record.config_type == 'brand' and not record.brand_id:
                raise ValidationError(_('Voor type "Per Merk" moet een merk geselecteerd worden.'))
            if record.config_type == 'category':
                if not hasattr(record, 'public_categ_id'):
                    raise ValidationError(_('Webshop categorieën zijn niet beschikbaar. Installeer website_sale module.'))
                if not record.public_categ_id:
                    raise ValidationError(_('Voor type "Per Webshop Categorie" moet een categorie geselecteerd worden.'))
    
    @api.constrains('margin_percentage')
    def _check_margin_percentage(self):
        """Controleer dat marge percentage positief is"""
        for record in self:
            if record.margin_percentage < 0:
                raise ValidationError(_('Marge percentage moet positief zijn.'))
    
    @api.constrains('brand_id')
    def _check_unique_config(self):
        """Voorkom dubbele configuraties voor hetzelfde merk of categorie"""
        for record in self:
            if record.brand_id:
                domain = [('id', '!=', record.id), ('active', '=', True), ('brand_id', '=', record.brand_id.id)]
                if self.search(domain, limit=1):
                    raise ValidationError(
                        _('Er bestaat al een actieve marge configuratie voor merk "%s".') % record.brand_id.name
                    )
            if hasattr(record, 'public_categ_id') and record.public_categ_id:
                domain = [('id', '!=', record.id), ('active', '=', True), ('public_categ_id', '=', record.public_categ_id.id)]
                if self.search(domain, limit=1):
                    raise ValidationError(
                        _('Er bestaat al een actieve marge configuratie voor categorie "%s".') % record.public_categ_id.name
                    )
    
    def name_get(self):
        """Custom display name"""
        result = []
        for record in self:
            if record.config_type == 'brand':
                name = f"{record.brand_name} - {record.margin_percentage}%"
            else:
                name = f"{record.category_name} - {record.margin_percentage}%"
            result.append((record.id, name))
        return result
