# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Marge overschrijving velden
    use_custom_margin = fields.Boolean(
        string='Gebruik Afwijkende Marge',
        default=False,
        help='Indien aangevinkt, wordt een afwijkende marge toegepast i.p.v. de standaard marge'
    )
    custom_margin_percentage = fields.Float(
        string='Afwijkende Marge %',
        help='Afwijkende marge percentage voor dit specifieke product'
    )
    margin_override_approved = fields.Boolean(
        string='Marge Afwijking Goedgekeurd',
        default=False,
        help='Geeft aan of de afwijkende marge is goedgekeurd'
    )
    margin_override_approved_by = fields.Many2one(
        'res.users',
        string='Goedgekeurd Door',
        readonly=True
    )
    margin_override_approved_date = fields.Date(
        string='Goedkeuringsdatum',
        readonly=True
    )
    margin_override_end_date = fields.Date(
        string='Einddatum Aanbieding',
        help='Datum waarop de afwijkende marge vervalt en de standaard marge weer wordt toegepast'
    )
    
    # Berekende velden
    applicable_margin_percentage = fields.Float(
        string='Toegepaste Marge %',
        compute='_compute_applicable_margin',
        store=True,
        help='De marge die daadwerkelijk wordt toegepast (standaard of afwijkend)'
    )
    margin_config_id = fields.Many2one(
        'product.margin.config',
        string='Marge Configuratie',
        compute='_compute_margin_config',
        store=True,
        help='De marge configuratie die van toepassing is op dit product'
    )
    calculated_list_price = fields.Float(
        string='Berekende Verkoopprijs',
        compute='_compute_calculated_list_price',
        store=True,
        help='Automatisch berekende verkoopprijs op basis van inkoopprijs en marge'
    )
    
    # Waarschuwingen
    has_margin_deviation = fields.Boolean(
        string='Heeft Marge Afwijking',
        compute='_compute_margin_deviation',
        store=True
    )
    margin_deviation_warning = fields.Char(
        string='Marge Waarschuwing',
        compute='_compute_margin_deviation',
        store=True
    )

    @api.depends('product_brand_id', 'public_categ_ids')
    def _compute_margin_config(self):
        """Bepaal de van toepassing zijnde marge configuratie"""
        for product in self:
            config = False
            
            # Eerst proberen op basis van merk
            if product.product_brand_id:
                config = self.env['product.margin.config'].search([
                    ('config_type', '=', 'brand'),
                    ('brand_id', '=', product.product_brand_id.id),
                    ('active', '=', True)
                ], limit=1)
            
            # Als geen merk config, probeer op basis van eerste webshop categorie
            if not config and product.public_categ_ids:
                for categ in product.public_categ_ids:
                    config = self.env['product.margin.config'].search([
                        ('config_type', '=', 'category'),
                        ('public_categ_id', '=', categ.id),
                        ('active', '=', True)
                    ], limit=1)
                    if config:
                        break
            
            product.margin_config_id = config

    @api.depends('use_custom_margin', 'custom_margin_percentage', 'margin_override_approved',
                 'margin_override_end_date', 'margin_config_id.margin_percentage')
    def _compute_applicable_margin(self):
        """Bepaal de daadwerkelijk toe te passen marge"""
        today = date.today()
        
        for product in self:
            # Check of custom marge nog geldig is
            if (product.use_custom_margin and 
                product.margin_override_approved and
                product.margin_override_end_date and
                product.margin_override_end_date < today):
                # Aanbieding is verlopen, reset naar standaard
                product.write({
                    'use_custom_margin': False,
                    'margin_override_approved': False,
                })
            
            # Bepaal toe te passen marge
            if (product.use_custom_margin and 
                product.margin_override_approved and
                (not product.margin_override_end_date or product.margin_override_end_date >= today)):
                product.applicable_margin_percentage = product.custom_margin_percentage
            elif product.margin_config_id:
                product.applicable_margin_percentage = product.margin_config_id.margin_percentage
            else:
                product.applicable_margin_percentage = 0.0

    @api.depends('standard_price', 'seller_ids', 'seller_ids.price', 'applicable_margin_percentage')
    def _compute_calculated_list_price(self):
        """Bereken de verkoopprijs op basis van inkoopprijs en marge
        
        Voor percentage < 100%: Marge formule (winst als % van verkoop)
          verkoopprijs = inkoopprijs / (1 - marge% / 100)
          Voorbeeld: 25% marge op €100 inkoop -> €100 / 0.75 = €133.33
        
        Voor percentage ≥ 100%: Markup formule (winst als % van inkoop)
          verkoopprijs = inkoopprijs × (1 + marge% / 100)
          Voorbeeld: 200% markup op €100 inkoop -> €100 × 3 = €300
        """
        for product in self:
            # Gebruik helper method om juiste inkoopprijs te krijgen
            purchase_price = product._get_purchase_price()
            
            if purchase_price and product.applicable_margin_percentage:
                if product.applicable_margin_percentage < 100:
                    # Normale marge formule: verkoop = inkoop / (1 - marge/100)
                    product.calculated_list_price = purchase_price / (1 - product.applicable_margin_percentage / 100)
                else:
                    # Hoge percentages: gebruik markup formule
                    # 200% = 3x inkoopprijs, 300% = 4x inkoopprijs, etc.
                    product.calculated_list_price = purchase_price * (1 + product.applicable_margin_percentage / 100)
            else:
                product.calculated_list_price = purchase_price

    def _get_purchase_price(self):
        """Helper: bepaal de inkoopprijs (eerst van leverancier, anders standard_price)"""
        self.ensure_one()
        
        # Probeer eerst leveranciersprijs te krijgen
        if self.seller_ids:
            # Neem de eerste (goedkoopste/belangrijkste) leverancier
            return self.seller_ids[0].price
        
        # Als geen leveranciersprijs, gebruik standard_price
        return self.standard_price

    @api.depends('use_custom_margin', 'margin_override_approved', 'margin_override_end_date')
    def _compute_margin_deviation(self):
        """Bepaal of er een marge afwijking actief is en genereer waarschuwing"""
        today = date.today()
        
        for product in self:
            has_deviation = (
                product.use_custom_margin and 
                product.margin_override_approved and
                (not product.margin_override_end_date or product.margin_override_end_date >= today)
            )
            product.has_margin_deviation = has_deviation
            
            if has_deviation:
                if product.margin_override_end_date:
                    product.margin_deviation_warning = _(
                        'LET OP: Dit product heeft een afwijkende marge van %s%% (standaard: %s%%). '
                        'Geldig tot %s. Goedgekeurd door %s op %s.'
                    ) % (
                        product.custom_margin_percentage,
                        product.margin_config_id.margin_percentage if product.margin_config_id else 'N/A',
                        product.margin_override_end_date.strftime('%d-%m-%Y'),
                        product.margin_override_approved_by.name if product.margin_override_approved_by else 'Onbekend',
                        product.margin_override_approved_date.strftime('%d-%m-%Y') if product.margin_override_approved_date else 'Onbekend'
                    )
                else:
                    product.margin_deviation_warning = _(
                        'LET OP: Dit product heeft een permanente afwijkende marge van %s%% (standaard: %s%%). '
                        'Goedgekeurd door %s op %s.'
                    ) % (
                        product.custom_margin_percentage,
                        product.margin_config_id.margin_percentage if product.margin_config_id else 'N/A',
                        product.margin_override_approved_by.name if product.margin_override_approved_by else 'Onbekend',
                        product.margin_override_approved_date.strftime('%d-%m-%Y') if product.margin_override_approved_date else 'Onbekend'
                    )
            else:
                product.margin_deviation_warning = False

    def action_apply_calculated_price(self):
        """Pas de berekende prijs toe als verkoopprijs"""
        for product in self:
            if product.calculated_list_price:
                product.list_price = product.calculated_list_price

    def action_request_margin_override(self):
        """Open wizard voor aanvragen marge afwijking"""
        self.ensure_one()
        
        if not self.margin_config_id:
            raise UserError(_('Er is geen standaard marge configuratie beschikbaar voor dit product. '
                            'Configureer eerst een marge voor het merk of de webshop categorie.'))
        
        return {
            'name': _('Marge Afwijking Aanvragen'),
            'type': 'ir.actions.act_window',
            'res_model': 'margin.override.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.id,
                'default_current_margin': self.margin_config_id.margin_percentage,
                'default_requested_margin': self.custom_margin_percentage or self.margin_config_id.margin_percentage,
            }
        }

    def cron_check_expired_margin_overrides(self):
        """Scheduled action om verlopen marge afwijkingen te resetten"""
        today = date.today()
        expired_products = self.search([
            ('use_custom_margin', '=', True),
            ('margin_override_approved', '=', True),
            ('margin_override_end_date', '<', today),
        ])
        
        for product in expired_products:
            product.write({
                'use_custom_margin': False,
                'margin_override_approved': False,
            })
            # Herbereken prijs
            product._compute_applicable_margin()
            product._compute_calculated_list_price()
        
        return True
