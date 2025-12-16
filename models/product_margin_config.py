# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductMarginConfig(models.Model):
    _name = 'product.margin.config'
    _description = 'Product Margin Configuration'
    _order = 'sequence, name'

    name = fields.Char(string='Naam', required=True)
    sequence = fields.Integer(string='Volgorde', default=10)
    active = fields.Boolean(string='Actief', default=True)
    
    # Type configuratie
    config_type = fields.Selection([
        ('brand', 'Per Merk'),
    ], string='Type', required=True, default='brand')
    
    # Relaties
    brand_id = fields.Many2one(
        'product.brand',
        string='Product Merk',
        ondelete='cascade',
    )
    
    # Marge configuratie
    margin_percentage = fields.Float(
        string='Marge %',
        required=True,
        help='Marge percentage dat wordt toegepast op de inkoopprijs'
    )
    
    # Computed velden voor display
    brand_name = fields.Char(related='brand_id.name', string='Merk', store=True)
    category_name = fields.Char(related='public_categ_id.name', string='Categorie', store=True)

    @api.constrains('config_type', 'brand_id')
    def _check_config_consistency(self):
        """Controleer dat de juiste velden zijn ingevuld per type"""
        for record in self:
            if record.config_type == 'brand' and not record.brand_id:
                raise ValidationError(_('Voor type "Per Merk" moet een merk geselecteerd worden.'))
    
    @api.constrains('margin_percentage')
    def _check_margin_percentage(self):
        """Controleer dat marge percentage positief is"""
        for record in self:
            if record.margin_percentage < 0:
                raise ValidationError(_('Marge percentage moet positief zijn.'))
    
    @api.constrains('brand_id')
    def _check_unique_config(self):
        """Voorkom dubbele configuraties voor hetzelfde merk"""
        for record in self:
            if record.brand_id:
                domain = [('id', '!=', record.id), ('active', '=', True), ('brand_id', '=', record.brand_id.id)]
                if self.search(domain, limit=1):
                    raise ValidationError(
                        _('Er bestaat al een actieve marge configuratie voor merk "%s".') % record.brand_id.name
                    )
    
    def name_get(self):
        """Custom display name"""
        result = []
        for record in self:
            name = f"{record.brand_name} - {record.margin_percentage}%"
            result.append((record.id, name))
        return result
