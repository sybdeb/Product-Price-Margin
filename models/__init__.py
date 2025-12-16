# -*- coding: utf-8 -*-

from . import product_margin_config
from . import product_template
from . import product_public_category

# Optional integration with webshop_catalog_dashboard
try:
    from . import webshop_catalog_dashboard
except ImportError:
    pass
