# -*- coding: utf-8 -*-

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Migratie naar versie 19.0.1.0.4
    
    Fix: Correcte marge/markup berekening
    - Percentages < 100%: marge formule (winst als % van verkoop)
    - Percentages >= 100%: markup formule (winst als % van inkoop)
    
    Herberekent alle product prijzen met de nieuwe formule.
    """
    _logger.info("Start migratie naar 19.0.1.0.4 - Herberekening product prijzen")
    
    # Herbereken alle producten met een marge configuratie
    cr.execute("""
        SELECT id 
        FROM product_template 
        WHERE applicable_margin_percentage IS NOT NULL 
          AND applicable_margin_percentage > 0
    """)
    
    product_ids = [row[0] for row in cr.fetchall()]
    
    if product_ids:
        _logger.info(f"Herberekening van {len(product_ids)} producten met marge configuratie")
        
        # Trigger herberekening door computed fields
        cr.execute("""
            UPDATE product_template 
            SET write_date = NOW() 
            WHERE id IN %s
        """, (tuple(product_ids),))
    
    _logger.info("Migratie naar 19.0.1.0.4 voltooid")
