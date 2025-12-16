# Product Price Margin

## Beschrijving

Deze Odoo 19 module berekent automatisch de verkoopprijs van producten op basis van de inkoopprijs en een geconfigureerde marge. De marge kan worden ingesteld per product merk of per webshop categorie.

## Features

### 1. Marge Configuratie
- **Per Merk**: Stel een standaard marge in voor alle producten van een specifiek merk
- **Per Webshop Categorie**: Stel een standaard marge in voor alle producten in een specifieke webshop categorie
- Automatische berekening: Verkoopprijs = Inkoopprijs × (1 + Marge%)

### 2. Afwijkende Marge per Product
- Mogelijkheid om per product af te wijken van de standaard marge
- Expliciete goedkeuringsflow vereist
- Automatische logging van wie, wanneer en waarom de afwijking is goedgekeurd
- Optionele einddatum voor "aanbiedingen"

### 3. Waarschuwingen & Meldingen
- Duidelijke visuele waarschuwing bij afwijkende marges
- Informatie over wie de afwijking heeft goedgekeurd
- Waarschuwing over einddatum van aanbieding

### 4. Automatische Verwerking
- Dagelijkse scheduled action controleert verlopen aanbiedingen
- Automatische terugval naar standaard marge na einddatum
- Herberekening van prijzen

## Installatie

### Vereisten
Deze module is afhankelijk van:
- `product` (Odoo core)
- `product_brand` (OCA module)
- `sale` (Odoo core)

### Installatiestappen
1. Kopieer de module naar uw Odoo addons directory
2. Update de app lijst: `Instellingen > Technisch > Database Structuur > Apps bijwerken`
3. Zoek naar "Product Price Margin" en installeer de module

## Gebruik

### Marge Configuratie Aanmaken

1. Ga naar **Verkoop > Marge Beheer > Marge Configuraties**
2. Klik op **Nieuw**
3. Vul de volgende velden in:
   - **Naam**: Beschrijvende naam voor de configuratie
   - **Type**: Kies "Per Merk" of "Per Webshop Categorie"
   - **Merk** of **Categorie**: Selecteer het relevante merk of categorie
   - **Marge %**: Voer het gewenste marge percentage in (bijv. 30 voor 30%)
4. Klik op **Opslaan**

### Automatische Prijsberekening

De module berekent automatisch de verkoopprijs wanneer:
- Een product een inkoopprijs heeft
- Het product gekoppeld is aan een merk of categorie met een marge configuratie

Op het product formulier zie je:
- **Marge Configuratie**: Welke configuratie van toepassing is
- **Toegepaste Marge %**: Het percentage dat wordt gebruikt
- **Berekende Verkoopprijs**: De automatisch berekende prijs
- **Pas Berekende Prijs Toe**: Knop om de berekende prijs over te nemen

### Afwijkende Marge Aanvragen

1. Open een product (met een bestaande marge configuratie)
2. Klik op de **Marge %** button in de button box (rechtsboven)
3. In de wizard:
   - **Gewenste Marge %**: Voer de afwijkende marge in
   - **Einddatum Aanbieding**: Kies wanneer de afwijking moet vervallen (optioneel)
   - **Reden voor Afwijking**: Leg uit waarom deze afwijking nodig is
4. Bekijk de berekende nieuwe prijzen en het prijsverschil
5. Vink het goedkeuringsvakje aan: "✓ Ik geef expliciet akkoord"
6. Klik op **Goedkeuren en Toepassen**

### Monitoring

#### Producten met Afwijkende Marge Vinden
- Ga naar de productlijst
- Gebruik het filter **Met Afwijkende Marge**

#### Waarschuwingen
- Producten met een actieve afwijking tonen een oranje waarschuwingsbalk
- De waarschuwing bevat:
  - Standaard vs. afwijkende marge
  - Wie heeft goedgekeurd en wanneer
  - Einddatum (indien van toepassing)

## Technische Details

### Modellen

#### product.margin.config
Configuratie van marges per merk of categorie.

**Belangrijke velden:**
- `config_type`: 'brand' of 'category'
- `brand_id`: Link naar product.brand
- `public_categ_id`: Link naar product.public.category
- `margin_percentage`: Het marge percentage

#### product.template (uitgebreid)
Uitbreiding van het product model met marge functionaliteit.

**Nieuwe velden:**
- `use_custom_margin`: Boolean, gebruikt custom marge
- `custom_margin_percentage`: Afwijkende marge %
- `margin_override_approved`: Is de afwijking goedgekeurd
- `margin_override_end_date`: Einddatum van de afwijking
- `applicable_margin_percentage`: Computed, daadwerkelijk toegepaste marge
- `calculated_list_price`: Computed, berekende verkoopprijs

#### margin.override.wizard
Wizard voor het aanvragen en goedkeuren van marge afwijkingen.

### Scheduled Actions

**Check Expired Margin Overrides**
- Draait dagelijks
- Controleert verlopen marge afwijkingen
- Reset automatisch naar standaard marge

### Berekeningen

**Verkoopprijs formule:**
```
Verkoopprijs = Inkoopprijs × (1 + Marge% / 100)
```

**Voorbeeld:**
- Inkoopprijs: €100
- Marge: 30%
- Verkoopprijs: €100 × (1 + 30/100) = €100 × 1.30 = €130

### Security

De module definieert drie toegangsniveaus:
- **User**: Alleen lezen van marge configuraties
- **Sales Person**: Lezen en bewerken van configuraties, aanvragen van afwijkingen
- **Sales Manager**: Volledige toegang inclusief verwijderen

## Tips & Best Practices

1. **Marge Hiërarchie**: De module geeft voorrang aan merk boven categorie
2. **Einddatum**: Gebruik altijd een einddatum voor tijdelijke acties
3. **Reden**: Documenteer altijd goed waarom een afwijking nodig is
4. **Monitoring**: Check regelmatig welke producten afwijkende marges hebben
5. **Automatisering**: Laat de scheduled action actief staan voor automatisch beheer

## Ondersteuning

Voor vragen of problemen:
- Check de documentatie in de module
- Bekijk de log berichten op het product
- Controleer de scheduled action logs

## Pricing

Deze module is commercieel beschikbaar. Zie [PRICING.md](PRICING.md) voor prijsinformatie en licentie opties.

**Korte samenvatting:**
- Standalone: €149 eenmalig
- Bundle (3 modules): €349 (bespaar €48)
- Subscription: €15/maand

Contact: sybren@nerbys.nl

## Licentie

LGPL-3 - Source code is beschikbaar, commercieel gebruik vereist licentie.

## Auteur

Sybren - Nerbys.nl

## Versie

19.0.1.0.0
