# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductMarginConfig(models.Model):
    """Extend ProductMarginConfig to add public_categ_id field when website_sale is installed"""
    _inherit = 'product.margin.config'
    
    public_categ_id = fields.Many2one(
        'product.public.category',
        string='Webshop Categorie',
        ondelete='cascade',
    )
    category_name = fields.Char(related='public_categ_id.name', string='Categorie', store=False)  # Odoo19: stored related translated fields not supported


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    margin_percentage = fields.Float(
        string='Standaard Marge %',
        help='Standaard marge percentage voor producten in deze categorie'
    )
    margin_config_id = fields.Many2one(
        'product.margin.config',
        string='Marge Configuratie',
        compute='_compute_margin_config',
        store=True
    )
    has_margin_config = fields.Boolean(
        string='Heeft Marge Config',
        compute='_compute_margin_config',
        store=True
    )
    
    # Supplier selection settings (related from margin_config)
    supplier_selection_mode = fields.Selection(
        related='margin_config_id.supplier_selection_mode',
        string='Leverancier Selectie Modus',
        readonly=False,
        store=True
    )
    min_stock_threshold = fields.Integer(
        related='margin_config_id.min_stock_threshold',
        string='Minimale Voorraad',
        readonly=False,
        store=True
    )
    fallback_no_stock = fields.Boolean(
        related='margin_config_id.fallback_no_stock',
        string='Fallback naar Geen Voorraad',
        readonly=False,
        store=True
    )
    supplier_tiebreaker = fields.Selection(
        related='margin_config_id.supplier_tiebreaker',
        string='Tie-breaker',
        readonly=False,
        store=True
    )

    @api.depends('margin_percentage')
    def _compute_margin_config(self):
        """Zoek of maak marge configuratie voor deze categorie"""
        MarginConfig = self.env['product.margin.config']
        
        for category in self:
            # Zoek bestaande configuratie
            config = MarginConfig.search([
                ('config_type', '=', 'category'),
                ('public_categ_id', '=', category.id)
            ], limit=1)
            
            category.margin_config_id = config
            category.has_margin_config = bool(config)

    def write(self, vals):
        """Update of maak marge configuratie bij wijziging percentage"""
        result = super().write(vals)
        
        if 'margin_percentage' in vals:
            MarginConfig = self.env['product.margin.config']
            
            for category in self:
                if category.margin_percentage > 0:
                    # Zoek bestaande config
                    config = MarginConfig.search([
                        ('config_type', '=', 'category'),
                        ('public_categ_id', '=', category.id)
                    ], limit=1)
                    
                    if config:
                        # Update bestaande
                        config.margin_percentage = category.margin_percentage
                    else:
                        # Maak nieuwe
                        MarginConfig.create({
                            'name': f'Marge {category.name}',
                            'config_type': 'category',
                            'public_categ_id': category.id,
                            'margin_percentage': category.margin_percentage,
                        })
                elif category.margin_config_id:
                    # Verwijder config als marge op 0 gezet
                    category.margin_config_id.unlink()
        
        return result
