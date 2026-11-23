"""
ml/horticulture_knowledge.py — Verified agronomic knowledge base for horticultural,
plantation, and non-field crops in AgroSmart.

Background:
  The prototype Decision Tree model (trained on Kaggle data) covers only seasonal
  annual field crops (cereals, legumes, cotton, sugarcane). Perennial fruit trees,
  palms, vines, and horticultural vegetables have fundamentally different nutrient
  dynamics: dosages are calibrated per tree/plant by age rather than uniform
  broadcasting per acre, and require ring-basin placement, organic manure baselines,
  and phenological split schedules.

This module provides authoritative nutritional packages of practices derived from:
  - Indian Council of Agricultural Research (ICAR) institutes:
      * ICAR-CISH (Central Institute for Subtropical Horticulture)
      * ICAR-CITH (Central Institute of Temperate Horticulture)
      * ICAR-NRCB (National Research Centre for Banana)
      * ICAR-NRCG (National Research Centre for Grapes)
      * ICAR-CCRI (Central Citrus Research Institute)
      * ICAR-NRCP (National Research Centre on Pomegranate)
      * ICAR-IIHR (Indian Institute of Horticultural Research)
      * ICAR-CPCRI (Central Plantation Crops Research Institute)
      * ICAR-CRIJAF (Central Research Institute for Jute and Allied Fibres)
      * ICAR-IIVR (Indian Institute of Vegetable Research)
  - State Agricultural Universities (SAUs) & Commodity Boards:
      * Coffee Board of India / Central Coffee Research Institute (CCRI)
      * Tamil Nadu Agricultural University (TNAU) Agritech Portal
      * Punjab Agricultural University (PAU) Fruit/Vegetable Guides
      * Dr. Y.S. Parmar University of Horticulture and Forestry (UHF Nauni)

Architecture Role:
  Phase 1: Knowledge-base storage, validation, lookup, and advisory synthesis.
  Phase 2: Hybrid routing in fertilizer_model.py (delegates unsupported crops here).
"""
from __future__ import annotations

import copy
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── Crop Synonyms and Aliases ──────────────────────────────────────────────────
HORTICULTURE_ALIASES: dict[str, str] = {
    # Citrus synonyms
    "citrus": "orange",
    "mandarin": "orange",
    "sweet orange": "orange",
    "sweet_orange": "orange",
    "santra": "orange",
    "mosambi": "orange",
    # Cucurbit synonyms
    "musk melon": "muskmelon",
    "water melon": "watermelon",
    "kharbooza": "muskmelon",
    "tarbooz": "watermelon",
    # Fruit tree synonyms
    "aam": "mango",
    "kela": "banana",
    "seb": "apple",
    "angoor": "grapes",
    "grape": "grapes",
    "anar": "pomegranate",
    "papita": "papaya",
    "nariyal": "coconut",
    # Plantation & fiber synonyms
    "patsan": "jute",
    "tossa jute": "jute",
    "white jute": "jute",
    "kafi": "coffee",
}

# ── Authoritative Horticultural Database ──────────────────────────────────────
HORTICULTURE_DATABASE: dict[str, dict[str, Any]] = {
    "mango": {
        "crop_key": "mango",
        "common_name": "Mango",
        "botanical_name": "Mangifera indica",
        "plant_type": "Perennial Fruit Tree (Orchard)",
        "verified": True,
        "authority_sources": [
            "ICAR - Central Institute for Subtropical Horticulture (CISH), Lucknow: Package of Practices for Mango Cultivation",
            "Tamil Nadu Agricultural University (TNAU) Agritech Portal - Horticultural Crops: Mango (Nutrient Management)",
            "National Horticulture Board (NHB), Ministry of Agriculture & Farmers Welfare, Govt of India",
        ],
        "application_geometry": (
            "Ring basin / circular trench along canopy drip line (1.5 to 2.5 m from trunk), "
            "incorporated into upper 15 cm soil. Never broadcast fertilizer across open orchard floor."
        ),
        "dosage_unit": "per_tree_per_year",
        "annual_schedule": {
            "young_stage": {
                "age_bracket": "Year 1 (establishment)",
                "fym_kg": 10.0,
                "n_g": 100.0,
                "p2o5_g": 50.0,
                "k2o_g": 100.0,
                "commercial_fertilizers": "Urea ~220 g, SSP ~310 g (or DAP ~110 g), MOP ~170 g",
            },
            "annual_increment": {
                "description": "Increase annually by this rate from Year 2 up to Year 10",
                "fym_kg": 5.0,
                "n_g": 100.0,
                "p2o5_g": 50.0,
                "k2o_g": 100.0,
            },
            "mature_stage": {
                "age_bracket": "Year 10 and older (full bearing)",
                "fym_kg": 50.0,
                "n_g": 1000.0,
                "p2o5_g": 500.0,
                "k2o_g": 1000.0,
                "commercial_fertilizers": "Urea ~2.17 kg, SSP ~3.12 kg (or DAP ~1.08 kg), MOP ~1.67 kg",
            },
        },
        "timing_and_splits": [
            "Split 1 (Post-harvest / onset of monsoon, June–July): Apply 100% FYM + 100% P2O5 + 100% K2O + 50% N to support post-harvest vegetative flush.",
            "Split 2 (Fruit development stage, February–March): Apply remaining 50% N to support fruit sizing.",
        ],
        "organic_manure": "Farm Yard Manure (FYM) or well-rotted compost (10 kg for Year 1, up to 50 kg for mature trees) applied during onset of monsoon.",
        "micronutrients": (
            "Foliar spray of 0.2% Borax / Boric acid (2 g/L) at pea stage to control internal fruit necrosis and black tip; "
            "0.5% Zinc sulphate (5 g/L) + 0.25% lime to correct little-leaf disorder."
        ),
        "special_cautions": (
            "STRICT CAUTION: Do NOT apply nitrogen during flower bud differentiation and panicle emergence "
            "(October to December). Excess nitrogen during flowering triggers vegetative shoots at the expense "
            "of flower panicles and increases malformation incidence."
        ),
        "missing_or_unverified_fields": [
            "High-density planting (HDP) / ultra-high density (UHDP / Meadow orchard) fertigation tables require localized field testing.",
        ],
    },

    "banana": {
        "crop_key": "banana",
        "common_name": "Banana",
        "botanical_name": "Musa spp. (Cavendish / AAA / AAB group)",
        "plant_type": "Perennial Giant Herbaceous Monocot",
        "verified": True,
        "authority_sources": [
            "ICAR - National Research Centre for Banana (NRCB), Tiruchirappalli: Integrated Nutrient Management in Banana",
            "TNAU Agritech Portal - Crop Production Guide (Horticulture: Banana)",
        ],
        "application_geometry": (
            "Circular trench / band 30 to 50 cm away from the pseudostem, lightly covered with soil and mulched. "
            "Fertigation via drip emitters is highly recommended."
        ),
        "dosage_unit": "per_plant_per_cycle",
        "annual_schedule": {
            "establishment_basal": {
                "stage": "Pit planting (Basal)",
                "fym_kg": 10.0,
                "neem_cake_g": 250.0,
                "p2o5_g": 60.0,
                "commercial_fertilizers": "Single Super Phosphate (SSP) ~375 g per pit",
            },
            "vegetative_and_shooting_doses": {
                "total_cycle_n_g": 200.0,
                "total_cycle_p2o5_g": 60.0,
                "total_cycle_k2o_g": 300.0,
                "commercial_fertilizers": "Urea ~435 g, SSP ~375 g, Muriate of Potash (MOP) ~500 g per plant",
            },
        },
        "timing_and_splits": [
            "Basal (at planting): 100% FYM + 100% P2O5 (SSP) + neem cake.",
            "Split 1 (30 days after planting - 2nd month): 25% N (~110 g Urea) + 20% K2O (~100 g MOP).",
            "Split 2 (75 days after planting - 3rd month): 25% N (~110 g Urea) + 20% K2O (~100 g MOP).",
            "Split 3 (120 days after planting - 5th month): 25% N (~110 g Urea) + 30% K2O (~150 g MOP).",
            "Split 4 (Shooting / bunch emergence - 7th month): 25% N (~110 g Urea) + 30% K2O (~150 g MOP).",
        ],
        "organic_manure": "10 to 15 kg well-composted farmyard manure or vermicompost per pit before planting.",
        "micronutrients": (
            "Foliar spray of 0.5% Zinc sulphate (ZnSO4), 0.2% Ferrous sulphate (FeSO4), 0.2% Copper sulphate (CuSO4), "
            "and 0.1% Boric acid at 3rd, 5th, and 7th month after planting to maximize bunch weight and finger length."
        ),
        "special_cautions": (
            "Banana is an exceptionally heavy potassium feeder. Potassium deficiency leads to weak bunch stalks, "
            "choke throat, and poor bunch filling. Never apply all fertilizers at once due to high leaching in porous soils."
        ),
        "missing_or_unverified_fields": [
            "Tissue culture versus conventional sucker fertigation titration models require regional soil salinity checks.",
        ],
    },

    "apple": {
        "crop_key": "apple",
        "common_name": "Apple",
        "botanical_name": "Malus domestica",
        "plant_type": "Temperate Deciduous Fruit Tree",
        "verified": True,
        "authority_sources": [
            "ICAR - Central Institute of Temperate Horticulture (CITH), Srinagar: Temperate Fruit Production Guide",
            "Dr. Y.S. Parmar University of Horticulture and Forestry (UHF Nauni), Solan: Package of Practices for Fruit Crops (Apple)",
            "Sher-e-Kashmir University of Agricultural Sciences and Technology (SKUAST-K): Apple Nutrition Advisory",
        ],
        "application_geometry": (
            "Broadcast uniformly across the drip basin 30 cm away from trunk up to tree canopy perimeter; "
            "lightly hoe into soil. In sloped hillside orchards, apply in crescent basins along contour lines."
        ),
        "dosage_unit": "per_tree_per_year",
        "annual_schedule": {
            "young_stage": {
                "age_bracket": "Year 1 (after planting)",
                "fym_kg": 10.0,
                "n_g": 70.0,
                "p2o5_g": 35.0,
                "k2o_g": 70.0,
                "commercial_fertilizers": "Urea ~150 g, SSP ~220 g, MOP ~115 g",
            },
            "annual_increment": {
                "description": "Increase annually by this rate from Year 2 to Year 10",
                "fym_kg": 4.0,
                "n_g": 70.0,
                "p2o5_g": 35.0,
                "k2o_g": 70.0,
            },
            "mature_stage": {
                "age_bracket": "Year 10 and older (mature bearing tree)",
                "fym_kg": 45.0,
                "n_g": 700.0,
                "p2o5_g": 350.0,
                "k2o_g": 700.0,
                "commercial_fertilizers": "Urea ~1.52 kg, SSP ~2.19 kg, MOP ~1.17 kg",
            },
        },
        "timing_and_splits": [
            "Dormant Season (December–January): Apply entire FYM + 100% P2O5 + 100% K2O in the tree basin before snow/winter rains.",
            "Pre-bloom / Bud burst (February–March): Apply 50% of annual N (approx. 760 g Urea for mature tree) 2–3 weeks before bud break.",
            "Post-petal fall (May): Apply remaining 50% N after fruit set to support fruit cell enlargement.",
        ],
        "organic_manure": "40 to 50 kg well-rotted FYM per mature tree incorporated during winter dormancy.",
        "micronutrients": (
            "Foliar spray of 0.1% Boric acid (1 g/L) at pink bud stage to promote pollen germination and fruit set. "
            "0.5% Calcium chloride (CaCl2) sprays at 4, 6, and 8 weeks after petal fall to prevent bitter pit disorder."
        ),
        "special_cautions": (
            "Apple soils in hill tracts are frequently acidic (pH < 5.8). Soil test for lime requirement (agricultural lime / dolomite) "
            "every 3 years. Avoid excessive nitrogen applications close to harvest, as it reduces fruit red coloration and storage shelf-life."
        ),
        "missing_or_unverified_fields": [
            "High-density dwarfing rootstocks (M9, MM106) fertigation schedules require custom spacing calculations.",
        ],
    },

    "grapes": {
        "crop_key": "grapes",
        "common_name": "Grapes",
        "botanical_name": "Vitis vinifera",
        "plant_type": "Perennial Woody Vine (Viticulture)",
        "verified": True,
        "authority_sources": [
            "ICAR - National Research Centre for Grapes (NRCG), Pune: Package of Practices for Grapes",
            "Mahatma Phule Krishi Vidyapeeth (MPKV), Rahuri: Viticulture Nutritional Guidelines",
            "TNAU Agritech Portal - Horticulture: Grapes",
        ],
        "application_geometry": (
            "Shallow trenches (15 cm depth) along the vine rows 45 to 60 cm from the trunk, or through drip fertigation. "
            "Cover immediately with cane mulch."
        ),
        "dosage_unit": "per_hectare_annual",
        "annual_schedule": {
            "mature_vineyard_annual": {
                "description": "Mature commercial vineyard (>3 years, yielding 20-25 t/ha)",
                "fym_tonnes_per_ha": 25.0,
                "total_n_kg_ha": 300.0,
                "total_p2o5_kg_ha": 100.0,
                "total_k2o_kg_ha": 350.0,
                "per_acre_equivalent": "FYM ~10 t, N ~120 kg, P2O5 ~40 kg, K2O ~140 kg per acre",
            },
        },
        "timing_and_splits": [
            "Foundation Pruning / Back Pruning (April - Vegetative cycle): Apply 60% of annual N (180 kg/ha) + 50% P2O5 (50 kg/ha) + 30% K2O (105 kg/ha) + full FYM.",
            "Forward Pruning / Fruit Pruning (October - Reproductive cycle): Apply remaining 40% N (120 kg/ha) + 50% P2O5 (50 kg/ha) + 70% K2O (245 kg/ha) to optimize berry sugar accumulation.",
        ],
        "organic_manure": "25 tonnes/hectare well-rotted cattle manure or sheep manure applied during April foundation pruning.",
        "micronutrients": (
            "Foliar spray of 0.2% Zinc sulphate (2 g/L) and 0.1% Borax (1 g/L) 10 days before bloom to prevent shot berries (millerandage). "
            "0.5% Magnesium sulphate (MgSO4) to prevent bunch stem necrosis during berry softening (veraison)."
        ),
        "special_cautions": (
            "CRITICAL CHLORIDE TOXICITY WARNING: Grapes are highly sensitive to chloride ions. "
            "NEVER use Muriate of Potash (KCl). Potassium MUST be supplied as Sulfate of Potash (SOP / 0-0-50 / K2SO4) "
            "or Potassium nitrate (13-0-45) to prevent leaf scorching and petiole necrosis."
        ),
        "missing_or_unverified_fields": [
            "Wine grape cultivars (Cabernet, Shiraz) require lower nitrogen levels than table grapes (Thompson Seedless).",
        ],
    },

    "orange": {
        "crop_key": "orange",
        "common_name": "Orange / Citrus (Mandarin & Sweet Orange)",
        "botanical_name": "Citrus sinensis / Citrus reticulata",
        "plant_type": "Subtropical Evergreen Fruit Tree",
        "verified": True,
        "authority_sources": [
            "ICAR - Central Citrus Research Institute (CCRI), Nagpur: Citrus Nutrition Management",
            "Punjab Agricultural University (PAU), Ludhiana: Package of Practices for Citrus (Kinnow)",
            "Dr. Panjabrao Deshmukh Krishi Vidyapeeth (PDKV), Akola: Nagpur Mandarin Guide",
        ],
        "application_geometry": (
            "Circular basin 1.0 to 2.0 m from trunk under tree drip perimeter. "
            "Keep the immediate trunk base (30 cm collar) completely free of fertilizer and standing water to prevent gummosis."
        ),
        "dosage_unit": "per_tree_per_year",
        "annual_schedule": {
            "young_stage": {
                "age_bracket": "Year 1 (young orchard)",
                "fym_kg": 10.0,
                "n_g": 150.0,
                "p2o5_g": 50.0,
                "k2o_g": 50.0,
                "commercial_fertilizers": "Urea ~325 g, SSP ~310 g, MOP ~85 g",
            },
            "annual_increment": {
                "description": "Increase annually from Year 2 until Year 8",
                "fym_kg": 5.0,
                "n_g": 100.0,
                "p2o5_g": 30.0,
                "k2o_g": 60.0,
            },
            "mature_stage": {
                "age_bracket": "Year 8 and older (full bearing)",
                "fym_kg": 50.0,
                "n_g": 800.0,
                "p2o5_g": 300.0,
                "k2o_g": 600.0,
                "commercial_fertilizers": "Urea ~1.74 kg, SSP ~1.88 kg, MOP ~1.00 kg",
            },
        },
        "timing_and_splits": [
            "Split 1 (January–February, prior to Ambia bahar bloom): 100% FYM + 100% P2O5 + 50% K2O + 33% N.",
            "Split 2 (May–June, fruit development): 33% N + 25% K2O.",
            "Split 3 (August–September, pre-harvest sizing): 33% N + 25% K2O.",
        ],
        "organic_manure": "40 to 50 kg farmyard manure or compost per mature tree applied in January.",
        "micronutrients": (
            "Citrus is extremely susceptible to micronutrient chlorosis / dieback. "
            "Apply foliar spray of CCRI micro-nutrient mixture or combine: 0.5% Zinc sulphate (5 g/L) + "
            "0.2% Manganese sulphate (2 g/L) + 0.2% Ferrous sulphate (2 g/L) + 0.2% Borax (2 g/L) neutralized with 0.5% hydrated lime."
        ),
        "special_cautions": (
            "Avoid deep tillage or hoeing within 1.5 m of citrus trunks as surface feeder roots are easily damaged. "
            "Prevent fertilizer contact with the trunk collar to guard against Phytophthora foot rot (gummosis)."
        ),
        "missing_or_unverified_fields": [
            "Rootstock interactions (Rough Lemon vs Carrizo Citrange) for calcareous soil pH > 8.0 require localized evaluation.",
        ],
    },

    "pomegranate": {
        "crop_key": "pomegranate",
        "common_name": "Pomegranate",
        "botanical_name": "Punica granatum",
        "plant_type": "Perennial Arid/Subtropical Fruit Shrub/Tree",
        "verified": True,
        "authority_sources": [
            "ICAR - National Research Centre on Pomegranate (NRCP), Solapur: Nutrient Management in Pomegranate (Bhagwa cultivar)",
            "Mahatma Phule Krishi Vidyapeeth (MPKV), Rahuri: Pomegranate Production Technology",
        ],
        "application_geometry": (
            "Ring basin under canopy (0.6 to 1.2 m from the crown) or drip fertigation. "
            "Lightly incorporate into top 10 cm of soil."
        ),
        "dosage_unit": "per_plant_per_year",
        "annual_schedule": {
            "young_stage": {
                "age_bracket": "Year 1 (juvenile plant)",
                "fym_kg": 10.0,
                "n_g": 125.0,
                "p2o5_g": 60.0,
                "k2o_g": 60.0,
                "commercial_fertilizers": "Urea ~270 g, SSP ~375 g, MOP ~100 g",
            },
            "mature_stage": {
                "age_bracket": "Year 5 and older (full commercial bearing)",
                "fym_kg": 30.0,
                "n_g": 625.0,
                "p2o5_g": 250.0,
                "k2o_g": 300.0,
                "commercial_fertilizers": "Urea ~1.36 kg, SSP ~1.56 kg, MOP ~500 g",
            },
        },
        "timing_and_splits": [
            "At Bahar Induction (crop regulation rest-break): Apply 100% FYM + 100% P2O5 + 50% K2O.",
            "First irrigation / Bud emergence: Apply 33% N.",
            "30 days after fruit set: Apply 33% N + 25% K2O.",
            "60 days after fruit set (fruit sizing): Apply remaining 34% N + 25% K2O.",
        ],
        "organic_manure": "25 to 30 kg farmyard manure or 5 kg vermicompost per plant at the end of the water-withholding rest period.",
        "micronutrients": (
            "Foliar spray of 0.2% Solubor (Boron 2 g/L) and 0.5% Zinc sulphate at flowering and fruit set "
            "to prevent fruit cracking and aril development disorder."
        ),
        "special_cautions": (
            "Unbalanced nitrogen or erratic soil moisture during fruit enlargement triggers severe rind cracking. "
            "High potassium and consistent moisture are essential for aril coloration and fruit integrity."
        ),
        "missing_or_unverified_fields": [
            "Bahar-specific scheduling (Mrig bahar vs Hasta bahar) in heavy black cotton soils requires localized drainage checks.",
        ],
    },

    "papaya": {
        "crop_key": "papaya",
        "common_name": "Papaya",
        "botanical_name": "Carica papaya",
        "plant_type": "Fast-growing Semi-woody Herbaceous Fruit Tree",
        "verified": True,
        "authority_sources": [
            "ICAR - Indian Institute of Horticultural Research (IIHR), Bengaluru: Cultivation Practices for Papaya",
            "TNAU Agritech Portal: Crop Production Guide - Horticulture (Papaya)",
        ],
        "application_geometry": (
            "Circular shallow furrow 40 to 80 cm from the stem. "
            "Keep 15 cm clear zone around the soft herbaceous stem to prevent collar rot."
        ),
        "dosage_unit": "per_plant_per_cycle",
        "annual_schedule": {
            "total_crop_cycle": {
                "duration": "18 to 24 months commercial cycle",
                "fym_kg": 15.0,
                "n_g": 250.0,
                "p2o5_g": 250.0,
                "k2o_g": 500.0,
                "commercial_fertilizers": "Urea ~540 g, SSP ~1.56 kg, MOP ~830 g per plant",
            },
        },
        "timing_and_splits": [
            "Basal at pit planting: 10 kg FYM + 100 g neem cake + 20% P2O5 (~300 g SSP).",
            "Top-dressing splits: Apply remaining N, P, and K in 6 bimonthly split applications (every 60 days) starting from 2nd month after transplanting.",
        ],
        "organic_manure": "10 to 15 kg well-rotted FYM or compost per pit at planting.",
        "micronutrients": (
            "Boron deficiency causes severe 'bumpy fruit' disorder and latex oozing from fruits. "
            "Apply 10 g Borax per plant in soil or foliar spray 0.1% Boric acid (1 g/L) at 4th and 6th month."
        ),
        "special_cautions": (
            "Papaya is extremely susceptible to waterlogging and collar rot (Phytophthora / Pythium). "
            "Ensure excellent surface drainage; never heap moist soil or fresh fertilizer against the stem collar."
        ),
        "missing_or_unverified_fields": [
            "Gynodioecious (Red Lady 786) versus dioecious varieties fertigation curves require local nursery confirmation.",
        ],
    },

    "coconut": {
        "crop_key": "coconut",
        "common_name": "Coconut",
        "botanical_name": "Cocos nucifera",
        "plant_type": "Perennial Monocot Plantation Palm",
        "verified": True,
        "authority_sources": [
            "ICAR - Central Plantation Crops Research Institute (CPCRI), Kasaragod: Package of Practices for Coconut Cultivation",
            "Coconut Development Board (CDB), Kochi: Fertilizer Recommendations for Coconut Palms",
        ],
        "application_geometry": (
            "Circular basin of 1.8 m radius around the palm trunk, dug 10–15 cm deep. "
            "Incorporate fertilizer and cover with green manure or dry coconut leaf mulch."
        ),
        "dosage_unit": "per_palm_per_year",
        "annual_schedule": {
            "young_stage": {
                "age_bracket": "Year 1 (young seedling)",
                "fym_kg": 10.0,
                "n_g": 125.0,
                "p2o5_g": 80.0,
                "k2o_g": 300.0,
                "commercial_fertilizers": "Urea ~270 g, Rock Phosphate ~400 g, MOP ~500 g",
            },
            "mature_stage": {
                "age_bracket": "Year 5 and older (mature bearing palm)",
                "fym_kg": 35.0,
                "n_g": 500.0,
                "p2o5_g": 320.0,
                "k2o_g": 1200.0,
                "mgso4_g": 500.0,
                "commercial_fertilizers": "Urea ~1.1 kg, Mussorie Rock Phosphate ~1.6 kg (or SSP ~2.0 kg), MOP ~2.0 kg, MgSO4 ~500 g",
            },
        },
        "timing_and_splits": [
            "Rainfed Palms (2 splits): Apply 1/3rd in May–June (pre-monsoon); apply remaining 2/3rd in September–October (post-monsoon).",
            "Irrigated Palms (4 splits): Divide annual dose into 4 equal splits applied in March, June, September, and December.",
        ],
        "organic_manure": "25 to 50 kg green manure / compost / FYM per palm per year applied with post-monsoon dose.",
        "micronutrients": (
            "Boron deficiency causes button shedding and crown choking ('crown rot' like disorder). "
            "Apply 50 g Borax per palm per year in circular basin. "
            "Magnesium sulphate (500 g/palm/year) is vital in acidic coastal/laterite soils to treat leaf yellowing."
        ),
        "special_cautions": (
            "Coconut requires large amounts of both Potassium and Chlorine for osmoregulation and high copra content. "
            "Muriate of Potash (KCl) is strictly preferred over Sulfate of Potash as chloride enhances nut retention."
        ),
        "missing_or_unverified_fields": [
            "Hybrid palms (Dwarf x Tall) yielding >150 nuts/year require a 25% higher fertilizer allowance.",
        ],
    },

    "coffee": {
        "crop_key": "coffee",
        "common_name": "Coffee (Arabica & Robusta)",
        "botanical_name": "Coffea arabica / Coffea canephora",
        "plant_type": "Perennial Woody Shade-grown Plantation Shrub",
        "verified": True,
        "authority_sources": [
            "Coffee Board of India / Central Coffee Research Institute (CCRI), Balehonnur: Coffee Guide - Nutrition & Manuring",
        ],
        "application_geometry": (
            "Broad band in drip circle under coffee bush canopy, applied over moist soil and covered with leaf litter. "
            "Do not pile fertilizer against the collar."
        ),
        "dosage_unit": "per_hectare_annual",
        "annual_schedule": {
            "arabica_mature": {
                "yield_baseline": "Mature Arabica yielding ~1 tonne clean coffee per hectare",
                "total_n_kg_ha": 140.0,
                "total_p2o5_kg_ha": 90.0,
                "total_k2o_kg_ha": 140.0,
                "per_acre_equivalent": "N ~56 kg, P2O5 ~36 kg, K2O ~56 kg per acre",
            },
        },
        "timing_and_splits": [
            "Pre-blossom (March): 40 kg N + 30 kg P2O5 + 40 kg K2O per ha to support blossom opening and initial flush.",
            "Post-blossom / Berry Development (May): 40 kg N + 0 kg P + 40 kg K2O per ha to support bean expansion.",
            "Mid-monsoon / Post-monsoon (September–October): 40 kg N + 30 kg P2O5 + 40 kg K2O per ha for wood ripening.",
            "Post-harvest (November–December): 20 kg N + 0 kg P + 20 kg K2O per ha to restore bush reserves.",
        ],
        "organic_manure": "Composted coffee pulp or cattle manure (5 tonnes/ha) applied in August–September.",
        "micronutrients": (
            "Pre-monsoon and post-monsoon foliar spray of 0.5% Zinc sulphate (5 g/L) + 0.5% Urea (5 g/L) "
            "to prevent rosette leaf formation and maintain canopy vigor."
        ),
        "special_cautions": (
            "Coffee soils are naturally acidic (pH 5.3 to 6.2). Apply agricultural lime or dolomite (500 to 1000 kg/ha) "
            "once every 2–3 years, at least 1 month BEFORE chemical fertilizers are applied."
        ),
        "missing_or_unverified_fields": [
            "Robusta vs Arabica differential nitrogen requirement under varied shade canopy density requires estate-level titration.",
        ],
    },

    "jute": {
        "crop_key": "jute",
        "common_name": "Jute (Tossa & White Jute)",
        "botanical_name": "Corchorus olitorius / Corchorus capsularis",
        "plant_type": "Annual Bast Fiber Crop",
        "verified": True,
        "authority_sources": [
            "ICAR - Central Research Institute for Jute and Allied Fibres (CRIJAF), Barrackpore: Improved Technologies for Jute Cultivation",
            "Directorate of Jute Development, Ministry of Agriculture & Farmers Welfare, Govt of India",
        ],
        "application_geometry": (
            "Basal dose broadcast and incorporated during final land preparation. "
            "Top-dressing applied by broadcasting between crop rows when soil is moist, followed by hand hoeing."
        ),
        "dosage_unit": "per_hectare_crop_season",
        "annual_schedule": {
            "tossa_jute_c_olitorius": {
                "n_kg_ha": 60.0,
                "p2o5_kg_ha": 30.0,
                "k2o_kg_ha": 30.0,
                "per_acre_equivalent": "N ~24 kg, P2O5 ~12 kg, K2O ~12 kg per acre (Urea ~52 kg, SSP ~75 kg, MOP ~20 kg per acre)",
            },
            "white_jute_c_capsularis": {
                "n_kg_ha": 80.0,
                "p2o5_kg_ha": 40.0,
                "k2o_kg_ha": 40.0,
                "per_acre_equivalent": "N ~32 kg, P2O5 ~16 kg, K2O ~16 kg per acre",
            },
        },
        "timing_and_splits": [
            "Basal (at final land preparation): 100% P2O5 + 100% K2O + 25% N.",
            "Top-dress 1 (3 to 4 weeks after sowing, after 1st weeding and thinning): 50% N.",
            "Top-dress 2 (5 to 6 weeks after sowing): Remaining 25% N.",
        ],
        "organic_manure": "5 tonnes/ha well-decomposed FYM or compost incorporated 2–3 weeks before sowing.",
        "micronutrients": "Soil application of 10 kg/ha Borax in boron-deficient alluvial tracts to prevent stem cracking.",
        "special_cautions": (
            "Excessive nitrogen application induces crop lodging, reduces fiber tensile strength, and increases susceptibility "
            "to stem rot (*Macrophomina phaseolina*). Adequate potassium is essential for fiber strength and bark thickness."
        ),
        "missing_or_unverified_fields": [
            "Waterlogged char land versus upland alluvial soil dose variations require field drainage assessments.",
        ],
    },

    "watermelon": {
        "crop_key": "watermelon",
        "common_name": "Watermelon",
        "botanical_name": "Citrullus lanatus",
        "plant_type": "Annual Warm-Season Trailing Cucurbit (Fruit vegetable)",
        "verified": True,
        "authority_sources": [
            "ICAR - Indian Institute of Vegetable Research (IIVR), Varanasi: Package of Practices for Cucurbitaceous Crops",
            "TNAU Agritech Portal: Crop Production Guide - Vegetables (Watermelon)",
            "Punjab Agricultural University (PAU), Ludhiana: Vegetable Production Technology",
        ],
        "application_geometry": (
            "Applied in planting pits or furrows along the irrigation beds. "
            "Top-dressing placed 10–15 cm away from the vine base."
        ),
        "dosage_unit": "per_hectare_crop_season",
        "annual_schedule": {
            "commercial_crop": {
                "fym_tonnes_ha": 25.0,
                "n_kg_ha": 100.0,
                "p2o5_kg_ha": 60.0,
                "k2o_kg_ha": 60.0,
                "per_acre_equivalent": "FYM ~10 t, N ~40 kg, P2O5 ~24 kg, K2O ~24 kg per acre (Urea ~87 kg, SSP ~150 kg, MOP ~40 kg per acre)",
            },
        },
        "timing_and_splits": [
            "Basal (at pit preparation): 100% FYM + 100% P2O5 + 100% K2O + 33% N.",
            "Top-dress 1 (Vine elongation stage, 30 days after sowing): 33% N (~29 kg Urea/acre).",
            "Top-dress 2 (Early fruit set stage, 45–50 days after sowing): Remaining 34% N (~29 kg Urea/acre).",
        ],
        "organic_manure": "20 to 25 tonnes/ha well-composted cattle manure incorporated into pits during land preparation.",
        "micronutrients": "Foliar spray of 0.2% Borax (2 g/L) at commencement of flowering to ensure proper pollination and prevent hollow heart.",
        "special_cautions": (
            "CEASE all nitrogen top-dressings once fruits reach half-mature size. "
            "Excess nitrogen during fruit development causes rind cracking, insipid white flesh, and poor fruit shelf-life. "
            "High potassium promotes rind thickness and higher sugar content (Brix)."
        ),
        "missing_or_unverified_fields": [
            "Mulched drip fertigation (fertigation every 3 days) schedule requires emitter spacing calibration.",
        ],
    },

    "muskmelon": {
        "crop_key": "muskmelon",
        "common_name": "Muskmelon",
        "botanical_name": "Cucumis melo",
        "plant_type": "Annual Warm-Season Trailing Cucurbit (Fruit vegetable)",
        "verified": True,
        "authority_sources": [
            "ICAR - Indian Institute of Vegetable Research (IIVR), Varanasi: Vegetable Production Guide",
            "Punjab Agricultural University (PAU), Ludhiana: Package of Practices for Muskmelon",
            "TNAU Agritech Portal: Crop Production Guide - Horticulture (Muskmelon)",
        ],
        "application_geometry": (
            "Applied in planting hills or furrows along the irrigation channels. "
            "Avoid direct contact with tender vine runners."
        ),
        "dosage_unit": "per_hectare_crop_season",
        "annual_schedule": {
            "commercial_crop": {
                "fym_tonnes_ha": 25.0,
                "n_kg_ha": 90.0,
                "p2o5_kg_ha": 60.0,
                "k2o_kg_ha": 60.0,
                "per_acre_equivalent": "FYM ~10 t, N ~36 kg, P2O5 ~24 kg, K2O ~24 kg per acre (Urea ~78 kg, SSP ~150 kg, MOP ~40 kg per acre)",
            },
        },
        "timing_and_splits": [
            "Basal (at pit/furrow preparation): 100% FYM + 100% P2O5 + 100% K2O + 33% N.",
            "Top-dress 1 (Vine running stage, 25–30 days after sowing): 33% N (~26 kg Urea/acre).",
            "Top-dress 2 (Flowering and initial fruit set, 45 days after sowing): Remaining 34% N (~26 kg Urea/acre).",
        ],
        "organic_manure": "20 to 25 tonnes/ha well-rotted farmyard manure mixed in planting furrows.",
        "micronutrients": (
            "Foliar spray of 0.1% Boron (1 g/L) + 0.2% Zinc sulphate (2 g/L) at early bloom "
            "to maximize female flower retention and uniform net formation on the rind."
        ),
        "special_cautions": (
            "Potassium is vital for sweetness (TSS > 11-12% Brix) and post-harvest shelf-life. "
            "Withhold or reduce irrigation 5 to 7 days prior to harvest to prevent fruit cracking and sugar dilution."
        ),
        "missing_or_unverified_fields": [
            "Protected cultivation / polyhouse net-house fertigation schedules require custom water electrical conductivity monitoring.",
        ],
    },
}


# ── Public API & Lookup Functions ─────────────────────────────────────────────

def normalize_crop_name(crop_name: str | None) -> str:
    """Normalize input crop string: strip whitespace, lowercase, and resolve aliases."""
    if not crop_name:
        return ""
    cleaned = str(crop_name).strip().lower()
    return HORTICULTURE_ALIASES.get(cleaned, cleaned)


def is_horticultural_crop(crop_name: str | None) -> bool:
    """
    Check if a crop belongs to the horticultural / plantation knowledge base.

    Returns True for any of the 12 unsupported crops (or their registered aliases).
    """
    norm = normalize_crop_name(crop_name)
    return norm in HORTICULTURE_DATABASE


def list_supported_horticultural_crops() -> list[str]:
    """Return sorted list of canonical crop keys in the horticultural database."""
    return sorted(list(HORTICULTURE_DATABASE.keys()))


def get_horticulture_profile(crop_name: str | None) -> dict[str, Any] | None:
    """
    Retrieve deep copy of the raw horticultural profile for the requested crop.

    Returns None if the crop is not found in the database.
    """
    norm = normalize_crop_name(crop_name)
    profile = HORTICULTURE_DATABASE.get(norm)
    if profile is None:
        return None
    return copy.deepcopy(profile)


def format_horticultural_advisory(crop_name: str | None,
                                  tree_age_years: int | None = None) -> dict[str, Any] | None:
    """
    Format a complete, scientifically validated agronomic advisory response
    for an unsupported horticultural or plantation crop.

    Args:
        crop_name:       Target crop (e.g. "mango", "banana", "apple")
        tree_age_years:  Optional age of tree in years (for orchard tree dosage calculation)

    Returns:
        Structured dictionary suitable for service responses, or None if crop unknown.
    """
    profile = get_horticulture_profile(crop_name)
    if profile is None:
        return None

    crop_key = profile["crop_key"]
    common_name = profile["common_name"]
    unit = profile.get("dosage_unit", "per_acre")

    # Build age-aware dosage summary
    if unit == "per_tree_per_year":
        if tree_age_years is not None and tree_age_years > 0:
            if tree_age_years == 1:
                stg = profile["annual_schedule"]["young_stage"]
                dose_summary = (
                    f"Year 1 Young Tree: {stg['fym_kg']:.0f} kg FYM, "
                    f"{stg['n_g']:.0f}g N, {stg['p2o5_g']:.0f}g P2O5, {stg['k2o_g']:.0f}g K2O "
                    f"({stg.get('commercial_fertilizers', '')})"
                )
            elif tree_age_years >= 10:
                mat = profile["annual_schedule"]["mature_stage"]
                dose_summary = (
                    f"Mature Tree (Age {tree_age_years}+): {mat['fym_kg']:.0f} kg FYM, "
                    f"{mat['n_g']:.0f}g N, {mat['p2o5_g']:.0f}g P2O5, {mat['k2o_g']:.0f}g K2O "
                    f"({mat.get('commercial_fertilizers', '')})"
                )
            else:
                inc = profile["annual_schedule"]["annual_increment"]
                base = profile["annual_schedule"]["young_stage"]
                n = base["n_g"] + inc["n_g"] * (tree_age_years - 1)
                p = base["p2o5_g"] + inc["p2o5_g"] * (tree_age_years - 1)
                k = base["k2o_g"] + inc["k2o_g"] * (tree_age_years - 1)
                fym = base["fym_kg"] + inc["fym_kg"] * (tree_age_years - 1)
                dose_summary = (
                    f"Tree Age {tree_age_years}: {fym:.0f} kg FYM, {n:.0f}g N, {p:.0f}g P2O5, {k:.0f}g K2O per tree/year."
                )
        else:
            mat = profile["annual_schedule"].get("mature_stage", {})
            dose_summary = (
                f"Mature Tree Baseline (Age 10+): {mat.get('fym_kg', 50):.0f} kg FYM, "
                f"{mat.get('n_g', 1000):.0f}g N, {mat.get('p2o5_g', 500):.0f}g P2O5, {mat.get('k2o_g', 1000):.0f}g K2O per tree/year "
                f"({mat.get('commercial_fertilizers', '')}). Calibrate based on orchard age."
            )
    elif unit == "per_plant_per_cycle":
        if crop_key == "banana":
            veg = profile["annual_schedule"]["vegetative_and_shooting_doses"]
            dose_summary = (
                f"Per Plant Baseline: 10–15 kg FYM, {veg['total_cycle_n_g']:.0f}g N, "
                f"{veg['total_cycle_p2o5_g']:.0f}g P2O5, {veg['total_cycle_k2o_g']:.0f}g K2O "
                f"({veg.get('commercial_fertilizers', '')})."
            )
        elif crop_key == "papaya":
            tot = profile["annual_schedule"]["total_crop_cycle"]
            dose_summary = (
                f"Per Plant Baseline: {tot['fym_kg']:.0f} kg FYM, {tot['n_g']:.0f}g N, "
                f"{tot['p2o5_g']:.0f}g P2O5, {tot['k2o_g']:.0f}g K2O "
                f"({tot.get('commercial_fertilizers', '')}) across 6 bimonthly splits."
            )
        else:
            dose_summary = f"Calibrated per plant per crop cycle. Consult package of practices."
    elif unit == "per_palm_per_year":
        mat = profile["annual_schedule"]["mature_stage"]
        dose_summary = (
            f"Mature Bearing Palm (Age 5+): {mat['fym_kg']:.0f} kg FYM, {mat['n_g']:.0f}g N, "
            f"{mat['p2o5_g']:.0f}g P2O5, {mat['k2o_g']:.0f}g K2O ({mat.get('commercial_fertilizers', '')})."
        )
    else:  # per_hectare or annual area basis
        sched = profile["annual_schedule"]
        first_key = list(sched.keys())[0]
        equiv = sched[first_key].get("per_acre_equivalent", "Area based application")
        dose_summary = f"Commercial Field Baseline: {equiv}."

    return {
        "status": "horticultural_guideline",
        "crop": crop_key,
        "common_name": common_name,
        "botanical_name": profile["botanical_name"],
        "plant_type": profile["plant_type"],
        "headline": f"Extension Package of Practices for {common_name}",
        "dosage_summary": dose_summary,
        "dosage_unit": unit,
        "application_method": profile["application_geometry"],
        "timing_and_splits": profile["timing_and_splits"],
        "organic_manure": profile["organic_manure"],
        "micronutrients": profile["micronutrients"],
        "special_cautions": profile["special_cautions"],
        "authority_sources": profile["authority_sources"],
        "verified": profile["verified"],
        "missing_or_unverified_fields": profile["missing_or_unverified_fields"],
    }
