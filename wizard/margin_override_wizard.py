# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date, timedelta


class MarginOverrideWizard(models.TransientModel):
    _name = 'margin.override.wizard'
    _description = 'Wizard voor Marge Afwijking Goedkeuring'

    product_id = fields.Many2one(
        'product.template',
        string='Product',
        required=True,
        readonly=True
    )
    product_name = fields.Char(
        related='product_id.name',
        string='Product Naam',
        readonly=True
    )
    current_margin = fields.Float(
        string='Huidige Standaard Marge %',
        readonly=True,
        help='De marge die normaal van toepassing is op dit product'
    )
    requested_margin = fields.Float(
        string='Gewenste Marge %',
        required=True,
        help='De afwijkende marge die u wilt toepassen'
    )
    end_date = fields.Date(
        string='Einddatum Aanbieding',
        help='Datum waarop de afwijking vervalt. Laat leeg voor permanente afwijking.',
        default=lambda self: date.today() + timedelta(days=30)
    )
    reason = fields.Text(
        string='Reden voor Afwijking',
        required=True,
        help='Leg uit waarom deze afwijkende marge nodig is'
    )
    
    # Berekende velden
    current_purchase_price = fields.Float(
        string='Huidige Inkoopprijs',
        compute='_compute_current_purchase_price',
        readonly=True,
        help='Inkoopprijs (eerst van leverancier, anders standard_price)'
    )
    current_sale_price = fields.Float(
        related='product_id.list_price',
        string='Huidige Verkoopprijs',
        readonly=True
    )
    calculated_new_price = fields.Float(
        string='Nieuwe Berekende Verkoopprijs',
        compute='_compute_calculated_new_price',
        help='De verkoopprijs die resulteert uit de gewenste marge'
    )
    manual_price = fields.Float(
        string='Handmatige Verkoopprijs',
        help='Vul hier handmatig een verkoopprijs in om de berekende prijs te overschrijven'
    )
    final_price = fields.Float(
        string='Toe te Passen Verkoopprijs',
        compute='_compute_final_price',
        help='De prijs die uiteindelijk wordt toegepast (handmatig of berekend)'
    )
    price_difference = fields.Float(
        string='Prijsverschil',
        compute='_compute_calculated_new_price',
        help='Het verschil tussen huidige en nieuwe verkoopprijs'
    )
    price_difference_percentage = fields.Float(
        string='Prijsverschil %',
        compute='_compute_calculated_new_price',
        help='Het procentuele verschil tussen huidige en nieuwe verkoopprijs'
    )
    
    # Goedkeuring
    requires_approval = fields.Boolean(
        string='Vereist Goedkeuring',
        default=True,
        help='Deze afwijking vereist expliciete goedkeuring'
    )
    approved = fields.Boolean(
        string='Goedgekeurd',
        default=False
    )

    @api.depends('product_id', 'product_id.standard_price', 'product_id.seller_ids')
    def _compute_current_purchase_price(self):
        """Bepaal de huidige inkoopprijs: eerst van leverancier, anders standard_price"""
        for wizard in self:
            purchase_price = 0.0
            
            # Probeer eerst leveranciersprijs te krijgen
            if wizard.product_id.seller_ids:
                # Neem de eerste (goedkoopste/belangrijkste) leverancier
                supplier = wizard.product_id.seller_ids[0]
                if supplier.price and supplier.price > 0:
                    purchase_price = supplier.price
            
            # Als geen leveranciersprijs, gebruik standard_price
            if not purchase_price or purchase_price == 0:
                purchase_price = wizard.product_id.standard_price
            
            wizard.current_purchase_price = purchase_price

    @api.depends('requested_margin', 'current_purchase_price', 'current_sale_price')
    def _compute_calculated_new_price(self):
        """Bereken de nieuwe verkoopprijs op basis van gewenste marge
        
        Voor percentage < 100%: Marge formule (winst als % van verkoop)
          verkoopprijs = inkoopprijs / (1 - marge% / 100)
          Voorbeeld: 25% marge op €100 inkoop -> €100 / 0.75 = €133.33
        
        Voor percentage ≥ 100%: Markup formule (winst als % van inkoop)
          verkoopprijs = inkoopprijs × (1 + marge% / 100)
          Voorbeeld: 200% markup op €100 inkoop -> €100 × 3 = €300
        """
        for wizard in self:
            if wizard.current_purchase_price and wizard.requested_margin is not False:
                if wizard.requested_margin < 100:
                    # Normale marge formule: verkoop = inkoop / (1 - marge/100)
                    wizard.calculated_new_price = wizard.current_purchase_price / (1 - wizard.requested_margin / 100)
                else:
                    # Hoge percentages: gebruik markup formule
                    # 200% = 3x inkoopprijs, 300% = 4x inkoopprijs, etc.
                    wizard.calculated_new_price = wizard.current_purchase_price * (1 + wizard.requested_margin / 100)
                
                wizard.price_difference = wizard.calculated_new_price - wizard.current_sale_price
                
                if wizard.current_sale_price:
                    wizard.price_difference_percentage = (wizard.price_difference / wizard.current_sale_price) * 100
                else:
                    wizard.price_difference_percentage = 0.0
            else:
                wizard.calculated_new_price = 0.0
                wizard.price_difference = 0.0
                wizard.price_difference_percentage = 0.0

    @api.depends('manual_price', 'calculated_new_price')
    def _compute_final_price(self):
        """Bepaal de uiteindelijk toe te passen prijs: handmatig of berekend"""
        for wizard in self:
            if wizard.manual_price and wizard.manual_price > 0:
                wizard.final_price = wizard.manual_price
            else:
                wizard.final_price = wizard.calculated_new_price

    @api.constrains('requested_margin')
    def _check_requested_margin(self):
        """Valideer dat de gewenste marge redelijk is"""
        for wizard in self:
            if wizard.requested_margin < 0:
                raise UserError(_('De marge mag niet negatief zijn.'))
            if wizard.requested_margin > 500:
                raise UserError(_('De marge van %s%% lijkt onrealistisch hoog. '
                                'Controleer uw invoer.') % wizard.requested_margin)

    @api.constrains('end_date')
    def _check_end_date(self):
        """Valideer dat einddatum in de toekomst ligt"""
        for wizard in self:
            if wizard.end_date and wizard.end_date < date.today():
                raise UserError(_('De einddatum moet in de toekomst liggen.'))

    def action_approve_and_apply(self):
        """Keur de marge afwijking goed en pas toe"""
        self.ensure_one()
        
        if not self.approved:
            raise UserError(_('U moet expliciet akkoord geven door het vinkje "Goedgekeurd" aan te vinken.'))
        
        # Update product met afwijkende marge
        self.product_id.write({
            'use_custom_margin': True,
            'custom_margin_percentage': self.requested_margin,
            'margin_override_approved': True,
            'margin_override_approved_by': self.env.user.id,
            'margin_override_approved_date': date.today(),
            'margin_override_end_date': self.end_date,
        })
        
        # Log de actie
        self.product_id.message_post(
            body=_(
                '<p><strong>Marge Afwijking Goedgekeurd</strong></p>'
                '<ul>'
                '<li>Standaard marge: %s%%</li>'
                '<li>Nieuwe marge: %s%%</li>'
                '<li>Goedgekeurd door: %s</li>'
                '<li>Einddatum: %s</li>'
                '<li>Reden: %s</li>'
                '</ul>'
            ) % (
                self.current_margin,
                self.requested_margin,
                self.env.user.name,
                self.end_date.strftime('%d-%m-%Y') if self.end_date else 'Permanent',
                self.reason
            )
        )
        
        # Pas de finale prijs direct toe (handmatig of berekend)
        if self.final_price:
            self.product_id.list_price = self.final_price
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Marge Afwijking Goedgekeurd'),
                'message': _('De afwijkende marge van %s%% is goedgekeurd en toegepast op product %s.') % (
                    self.requested_margin, self.product_name
                ),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_cancel(self):
        """Annuleer de wizard"""
        return {'type': 'ir.actions.act_window_close'}
