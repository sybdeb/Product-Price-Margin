# -*- coding: utf-8 -*-

def migrate(cr, version):
    """Remove public_categ_id field if it exists"""
    # Check if column exists
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='product_margin_config' 
        AND column_name='public_categ_id'
    """)
    
    if cr.fetchone():
        # Drop the column
        cr.execute("""
            ALTER TABLE product_margin_config 
            DROP COLUMN IF EXISTS public_categ_id
        """)
        
    # Also remove any category-type configs
    cr.execute("""
        DELETE FROM product_margin_config 
        WHERE config_type = 'category'
    """)
