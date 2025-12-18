# -*- coding: utf-8 -*-
{
    'name': 'Product Price Margin',
    'version': '19.0.1.0.10',
    'category': 'Sales',
    'summary': 'Automatische verkoopprijs berekening op basis van inkoopprijs en marge',
    'description': """
Product Price Margin
====================

Deze module berekent automatisch de verkoopprijs op basis van:
- Inkoopprijs (standard_price)
- Marge percentage per merk of webshop categorie
- Mogelijkheid tot afwijkende marge per product met goedkeuring en einddatum

Features:
---------
* Marge configuratie per product merk
* Marge configuratie per webshop categorie
* Product-specifieke marge met goedkeuringsflow
* Automatische terugval naar standaard marge na einddatum aanbieding
* Waarschuwingen bij afwijkende marges
    """,
    'author': 'Sybren',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'product',
        'product_brand',
        'sale',
        'website_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_margin_config_views.xml',
        'views/product_template_views.xml',
        'views/product_public_category_views.xml',
        'wizard/margin_override_wizard_views.xml',
        'data/ir_cron.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
