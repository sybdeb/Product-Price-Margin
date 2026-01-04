# Product Price Margin Module - Technisch Overzicht

**Module:** `product_price_margin`  
**Versie:** 19.0.1.0.13  
**Odoo Versie:** 19.0

## 📋 Doel

Automatische berekening van verkoopprijzen op basis van inkoopprijs en configureerbare marges per merk of webshop categorie, met intelligente leverancier selectie en voorraad management.

---

## 🔧 Gewijzigde/Uitgebreide Odoo Modellen

### 1. `product.template` (Product Template)

#### Toegevoegde Velden:

**Marge Configuratie:**
- `margin_config_id` (Many2one → product.margin.config) - Bepaalde marge configuratie
- `applicable_margin_percentage` (Float) - Toepasselijke marge % (computed)
- `calculated_list_price` (Float) - Automatisch berekende verkoopprijs (computed)

**Afwijkende Marge:**
- `use_custom_margin` (Boolean) - Product gebruikt afwijkende marge
- `custom_margin_percentage` (Float) - Afwijkende marge %
- `margin_override_approved` (Boolean) - Afwijking goedgekeurd
- `margin_override_approved_by` (Many2one → res.users) - Goedgekeurd door
- `margin_override_approved_date` (Date) - Goedkeuring datum
- `margin_override_end_date` (Date) - Einddatum afwijking
- `has_margin_deviation` (Boolean) - Heeft actieve afwijking (computed)
- `margin_deviation_warning` (Text) - Waarschuwing tekst (computed)

#### Methoden:

```python
def _compute_margin_config(self)
    """Bepaal toepasselijke marge config op basis van merk of categorie"""

def _compute_calculated_list_price(self)
    """Bereken verkoopprijs: 
    - Margin < 100%: price / (1 - margin)  [echte marge]
    - Markup >= 100%: price * (1 + markup) [markup formule]
    """

def _get_purchase_price(self)
    """Bepaal inkoopprijs in volgorde:
    1. Eigen voorraad > 0 → voorraadwaarde / qty
    2. seller_ids[0] (laagste sequence = voorkeur leverancier)
    3. Fallback → standard_price
    """

def update_supplier_sequences(self)
    """Update leverancier volgorde op basis van marge config regels:
    - auto_price: goedkoopste eerst
    - auto_price_stock: goedkoopste met voldoende voorraad
    - manual: bewaar huidige sequence
    """

def action_recalculate_price(self)
    """Forceer herberekening van verkoopprijs"""

def action_apply_calculated_price(self)
    """Pas berekende prijs toe als list_price"""

def action_request_margin_override(self)
    """Open wizard voor afwijkende marge aanvragen"""
```

---

### 2. `product.supplierinfo` (Supplier Info)

#### Toegevoegde Velden:
- `supplier_stock` (Integer) - Voorraad bij leverancier

#### Methoden Override:

```python
def write(self, vals)
    """Trigger price/sequence update bij wijziging van:
    - price
    - supplier_stock
    → Roept product_template.update_supplier_sequences() aan
    """

def create(self, vals_list)
    """Trigger sequence update bij nieuwe leverancier"""
```

---

### 3. `product.public.category` (Website Categorie)

#### Toegevoegde Velden:

**Marge:**
- `margin_percentage` (Float) - Standaard marge % voor deze categorie
- `margin_config_id` (Many2one → product.margin.config) - Gekoppelde marge config
- `has_margin_config` (Boolean) - Heeft configuratie (computed)

**Leverancier Selectie (related fields):**
- `supplier_selection_mode` (Selection) - auto_price / auto_price_stock / manual
- `min_stock_threshold` (Integer) - Minimale voorraad voor auto_price_stock
- `fallback_no_stock` (Boolean) - Fallback naar leveranciers zonder voorraad
- `supplier_tiebreaker` (Selection) - Tie-breaker: stock / delivery / keep

---

## 🆕 Nieuwe Modellen

### `product.margin.config` (Marge Configuratie)

**Doel:** Centrale configuratie van marges en leverancier selectie per merk of categorie.

#### Velden:

**Basis:**
- `name` (Char, required) - Configuratie naam
- `sequence` (Integer) - Volgorde (laagste = hoogste prioriteit)
- `active` (Boolean) - Actief/gearchiveerd
- `config_type` (Selection, required) - 'brand' of 'category'

**Marge:**
- `margin_percentage` (Float, required) - Marge percentage (als decimaal: 0.25 = 25%)

**Koppelingen:**
- `brand_id` (Many2one → product.brand) - Voor merk-specifieke configuratie
- `public_categ_id` (Many2one → product.public.category) - Voor categorie configuratie
- `brand_name` (Char, related) - Merk naam (display)
- `category_name` (Char, related) - Categorie naam (display)

**Leverancier Selectie:**
- `supplier_selection_mode` (Selection, default='auto_price_stock'):
  - `'auto_price'`: Goedkoopste leverancier (negeer voorraad)
  - `'auto_price_stock'`: Goedkoopste met voldoende voorraad
  - `'manual'`: Handmatig via drag-and-drop sequence
  
- `min_stock_threshold` (Integer, default=5) - Minimale voorraad voor auto_price_stock

- `fallback_no_stock` (Boolean, default=True) - Bij geen stock: fallback naar goedkoopste zonder voorraad

- `supplier_tiebreaker` (Selection, default='stock') - Bij gelijke prijs:
  - `'stock'`: Meeste voorraad eerst
  - `'delivery'`: Kortste levertijd eerst
  - `'keep'`: Behoud huidige volgorde

#### Constraints:
- Uniek per merk: brand_id moet uniek zijn
- Uniek per categorie: public_categ_id moet uniek zijn
- Één van beiden verplicht: brand_id OF public_categ_id moet gevuld zijn

---

### `margin.override.wizard` (Transient Model)

**Doel:** Wizard voor aanvragen/goedkeuren van afwijkende marges.

#### Velden:

**Product Info:**
- `product_id` (Many2one → product.template, required, readonly)
- `product_name` (Char, related)
- `current_purchase_price` (Float, computed) - Huidige inkoopprijs
- `current_sale_price` (Float, related) - Huidige verkoopprijs

**Marge:**
- `current_margin` (Float, readonly) - Huidige standaard marge
- `requested_margin` (Float, required) - Gewenste afwijkende marge
- `end_date` (Date, default=+30 dagen) - Einddatum aanbieding

**Berekeningen:**
- `calculated_new_price` (Float, computed) - Nieuwe verkoopprijs
- `price_difference` (Float, computed) - Verschil met huidige prijs
- `price_difference_percentage` (Float, computed) - % verschil

**Goedkeuring:**
- `reason` (Text, required) - Reden voor afwijking
- `requires_approval` (Boolean, default=True)
- `approved` (Boolean) - Expliciete goedkeuring

#### Methoden:

```python
def action_approve_override(self)
    """Pas afwijkende marge toe op product + log goedkeuring"""

def action_reject_override(self)
    """Sluit wizard zonder wijzigingen"""
```

---

## 🔄 Automatische Processen

### 1. **Cron Job: Prijzen Herberekenen**
- **Frequentie:** Elk uur
- **Actie:** `product.template.cron_recalculate_prices()`
- **Doel:** 
  - Herbereken alle product prijzen
  - Verwijder verlopen marge afwijkingen

### 2. **Trigger: Leverancier Wijziging**
- **Wanneer:** product.supplierinfo write/create
- **Wat:** price, supplier_stock, of active wijzigt
- **Actie:** Update supplier sequences op alle gekoppelde producten

### 3. **Trigger: Marge Config Wijziging**
- **Wanneer:** product.margin.config wijzigt
- **Actie:** Herbereken alle producten met deze config

---

## 📊 Berekeningslogica

### Prijsberekening Formules:

```python
# Bepaal inkoopprijs
if product.qty_available > 0 and product.stock_value > 0:
    purchase_price = product.stock_value / product.qty_available
elif product.seller_ids:
    purchase_price = product.seller_ids[0].price  # Eerste = voorkeur (laagste sequence)
else:
    purchase_price = product.standard_price

# Bereken verkoopprijs
if margin_percentage < 1.0:  # Margin formule
    sale_price = purchase_price / (1 - margin_percentage)
else:  # Markup formule  
    sale_price = purchase_price * (1 + margin_percentage)
```

### Leverancier Sequence Update:

```python
# Auto Price Stock mode
suitable_suppliers = suppliers_with_price.filtered(
    lambda s: s.supplier_stock >= config.min_stock_threshold
)

if not suitable_suppliers and config.fallback_no_stock:
    suitable_suppliers = suppliers_with_price  # Fallback

# Sorteer met tie-breaker
if config.supplier_tiebreaker == 'stock':
    key = (price, -supplier_stock, delay, id)
elif config.supplier_tiebreaker == 'delivery':
    key = (price, delay, -supplier_stock, id)
else:  # keep
    key = (price, sequence, id)

sorted_suppliers = sorted(suitable_suppliers, key=key)

# Update sequences (1 = eerste/voorkeur)
for index, supplier in enumerate(sorted_suppliers, start=1):
    supplier.sequence = index
```

---

## 🎯 Use Cases voor Andere Modules

### Als je een module ontwikkelt die:

**1. Product prijzen wijzigt:**
```python
# Trigger herberekening
product.action_recalculate_price()
# Of direct toepassen
product.action_apply_calculated_price()
```

**2. Leverancier info importeert:**
```python
# Automatische sequence update gebeurt via write/create triggers
supplierinfo.write({
    'price': 100.50,
    'supplier_stock': 25,
    'active': True
})
# → product.update_supplier_sequences() wordt automatisch aangeroepen
```

**3. Marge wil bepalen voor een product:**
```python
# Lees de berekende waarden
margin = product.applicable_margin_percentage  # Decimal: 0.25 = 25%
calculated_price = product.calculated_list_price
has_deviation = product.has_margin_deviation
```

**4. Voorraad synchroniseert:**
```python
# Update supplier stock → trigger sequence update
for supplier in product.seller_ids:
    supplier.supplier_stock = external_api.get_stock(supplier.partner_id)
# Sequences worden automatisch bijgewerkt
```

---

## 🔗 Dependencies

**Vereiste Modules:**
- `product` - Basis product management
- `product_brand` - Product merken (OCA module)
- `sale` - Verkoop module
- `website_sale` - Webshop functionaliteit

---

## 📁 Views & Menu's

**Menu Structuur:**
```
Verkoop
└── Configuratie
    └── Marge Configuraties (product.margin.config)
```

**Product Views:**
- Product form: Nieuwe tab "Marge Berekening"
- Leverancier list: Sequence handle + active toggle + stock

**Website Categorie Views:**
- Form: Secties "Marge Configuratie" en "Leverancier Selectie"

---

## 🔐 Security

**Access Rights:**
- `product.margin.config`: Verkoop Manager (volledig) / Gebruiker (read)
- `margin.override.wizard`: Verkoop Manager (volledig)
- Views: `base.group_user` (zichtbaar voor interne gebruikers)

---

## 🧪 Testen

**Database Test:**
```sql
-- Check marge configs
SELECT id, name, margin_percentage, supplier_selection_mode 
FROM product_margin_config WHERE active = true;

-- Check product met berekende prijs
SELECT pt.name, pt.list_price, pt.calculated_list_price, 
       pt.applicable_margin_percentage
FROM product_template pt WHERE id = 12;

-- Check leverancier sequences
SELECT si.sequence, rp.name, si.price, si.supplier_stock
FROM product_supplierinfo si 
JOIN res_partner rp ON si.partner_id = rp.id
WHERE si.product_tmpl_id = 12
ORDER BY si.sequence;
```

---

## 📝 Belangrijk voor Integraties

1. **Marges zijn decimalen:** 25% wordt opgeslagen als `0.25` (niet als `25`)
2. **Sequence = voorkeur:** Laagste sequence (1) = voorkeursleverancier
3. **Auto-updates:** Leverancier wijzigingen triggeren automatisch sequence updates
4. **Computed fields:** `calculated_list_price` en `applicable_margin_percentage` zijn read-only
5. **Prijs = actief:** Leveranciers zonder prijs (price = 0) worden genegeerd bij selectie

---

**Laatste Update:** 2026-01-04  
**Auteur:** Sybren
