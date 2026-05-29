#!/usr/bin/env python3
"""Post-process English pharmacology CSVs: fix abbreviations, capitalization, and academic style."""

import csv, re, sys, os

# Known pharmacology abbreviations (full term -> abbreviation)
ABBREVIATIONS = {
    "pharmacodynamics": "PD",
    "pharmacokinetics": "PK",
    "pharmacokinetic": "PK",
    "structure-activity relationship": "SAR",
    "angiotensin-converting enzyme": "ACE",
    "angiotensin ii": "Ang II",
    "angiotensin i": "Ang I",
    "renin-angiotensin-aldosterone system": "RAAS",
    "adverse drug reaction": "ADR",
    "minimum inhibitory concentration": "MIC",
    "minimum bactericidal concentration": "MBC",
    "chemotherapeutic index": "CI",
    "half maximal effective concentration": "EC50",
    "half maximal inhibitory concentration": "IC50",
    "half lethal dose": "LD50",
    "half effective dose": "ED50",
    "therapeutic index": "TI",
    "central nervous system": "CNS",
    "gastrointestinal": "GI",
    "angiotensin receptor blocker": "ARB",
    "angiotensin receptor blockers": "ARBs",
    "ace inhibitor": "ACEI",
    "ace inhibitors": "ACEIs",
    "calcium channel blocker": "CCB",
    "calcium channel blockers": "CCBs",
    "beta-blocker": "beta-blocker",
    "beta-blockers": "beta-blockers",
    "penicillin-binding protein": "PBP",
    "penicillin-binding proteins": "PBPs",
    "methicillin-resistant staphylococcus aureus": "MRSA",
    "extended-spectrum beta-lactamase": "ESBL",
    "extended-spectrum beta-lactamases": "ESBLs",
    "nonsteroidal anti-inflammatory drug": "NSAID",
    "nonsteroidal anti-inflammatory drugs": "NSAIDs",
    "proton pump inhibitor": "PPI",
    "proton pump inhibitors": "PPIs",
    "serotonin-norepinephrine reuptake inhibitor": "SNRI",
    "serotonin-norepinephrine reuptake inhibitors": "SNRIs",
    "selective serotonin reuptake inhibitor": "SSRI",
    "selective serotonin reuptake inhibitors": "SSRIs",
    "monoamine oxidase inhibitor": "MAOI",
    "monoamine oxidase inhibitors": "MAOIs",
    "tricyclic antidepressant": "TCA",
    "tricyclic antidepressants": "TCAs",
    "dihydropyridine": "DHP",
    "dihydropyridines": "DHPs",
    "human immunodeficiency virus": "HIV",
    "acquired immunodeficiency syndrome": "AIDS",
    "cytochrome p450": "CYP450",
    "glucagon-like peptide-1": "GLP-1",
    "sodium-glucose cotransporter 2": "SGLT2",
    "sodium-glucose cotransporter-2": "SGLT2",
    "dipeptidyl peptidase-4": "DPP-4",
    "dipeptidyl peptidase 4": "DPP-4",
    "5-fluorouracil": "5-FU",
    "5-fluorodeoxyuridine monophosphate": "5-FdUMP",
    "5-fluorouridine triphosphate": "5-FUTP",
    "thyroid-stimulating hormone": "TSH",
    "luteinizing hormone": "LH",
    "follicle-stimulating hormone": "FSH",
    "adrenocorticotropic hormone": "ACTH",
    "growth hormone": "GH",
    "gamma-aminobutyric acid": "GABA",
    "nitric oxide": "NO",
    "prostaglandin i2": "PGI2",
    "prostaglandin e2": "PGE2",
    "cyclic adenosine monophosphate": "cAMP",
    "cyclic guanosine monophosphate": "cGMP",
    "adenosine triphosphate": "ATP",
    "reactive oxygen species": "ROS",
    "cerebrospinal fluid": "CSF",
    "glomerular filtration rate": "GFR",
    "blood-brain barrier": "BBB",
    "antidiuretic hormone": "ADH",
    "atrial natriuretic peptide": "ANP",
    "brain natriuretic peptide": "BNP",
    "deoxyribonucleic acid": "DNA",
    "ribonucleic acid": "RNA",
    "messenger rna": "mRNA",
    "transfer rna": "tRNA",
    "body mass index": "BMI",
    "half-life": "t1/2",
    "bioavailability": "F",
    "volume of distribution": "Vd",
    "clearance": "CL",
    "maximum concentration": "Cmax",
    "time to maximum concentration": "Tmax",
    "area under the curve": "AUC",
    "absorption, distribution, metabolism, and excretion": "ADME",
}

# Drug names that should always be capitalized (first letter)
# Format: lowercase -> Proper case
DRUG_NAMES = {
    "penicillin g": "penicillin G",
    "penicillin v": "penicillin V",
    "benzathine penicillin": "benzathine penicillin",
    "procaine penicillin": "procaine penicillin",
    "amphotericin b": "amphotericin B",
    "liposomal amphotericin b": "liposomal amphotericin B",
    "nystatin": "nystatin",
    "griseofulvin": "griseofulvin",
    "flucytosine": "flucytosine",
    "fluconazole": "fluconazole",
    "itraconazole": "itraconazole",
    "voriconazole": "voriconazole",
    "posaconazole": "posaconazole",
    "ketoconazole": "ketoconazole",
    "clotrimazole": "clotrimazole",
    "miconazole": "miconazole",
    "econazole": "econazole",
    "terbinafine": "terbinafine",
    "caspofungin": "caspofungin",
    "micafungin": "micafungin",
    "anidulafungin": "anidulafungin",
    "flucytosine": "flucytosine",
    "amphotericin": "amphotericin",
}

# "Term (lowercase_term)" pattern fix: add abbreviation on first occurrence
def fix_term_parentheses(text):
    """Fix 'Pharmacodynamics (pharmacodynamics)' -> 'Pharmacodynamics (PD)'"""
    for full, abbr in ABBREVIATIONS.items():
        # Pattern: "Full Term (full_term)" where full_term is lowercase version
        pattern = re.compile(
            r'\b(' + re.escape(full) + r')\s*\(' + re.escape(full) + r'\)',
            re.IGNORECASE
        )
        # Capitalize first letter, add abbreviation in parens
        def repl(m):
            term = m.group(1)
            # Capitalize first letter
            term_cap = term[0].upper() + term[1:] if term[0].islower() else term
            return f"{term_cap} ({abbr})"
        text = pattern.sub(repl, text)
    return text


def fix_full_english_name(text):
    """Fix 'The full English name of pharmacodynamics is' -> abbreviation in question"""
    for full, abbr in ABBREVIATIONS.items():
        if len(abbr) <= 3 and full not in ("pharmacodynamics", "pharmacokinetics"):
            continue
        # Pattern: "full English name of <term>"
        pattern = re.compile(
            r'(full English name of\s+)(' + re.escape(full) + r')(\s+is)',
            re.IGNORECASE
        )
        def repl(m):
            prefix = m.group(1)
            term = m.group(2).strip()
            suffix = m.group(3)
            term_cap = term[0].upper() + term[1:] if term and term[0].islower() else term
            return f"{prefix}{term_cap}{suffix}"
        text = pattern.sub(repl, text)
    return text


def fix_drug_capitalization(text):
    """Ensure drug names have consistent capitalization."""
    # Most drug names are already lowercase in the CSVs (generic names)
    # Only fix specific known patterns where capitalization matters
    fixes = [
        # Vitamin K is always capitalized
        (r'\bvitamin k\b', 'vitamin K'),
        # Amphotericin B
        (r'\bamphotericin b\b', 'amphotericin B'),
        # Penicillin G/V
        (r'\bpenicillin g\b', 'penicillin G'),
        (r'\bpenicillin v\b', 'penicillin V'),
        # Various B vitamins
        (r'\bvitamin b(\d+)\b', r'vitamin B\1'),
        (r'\bvitamin d\b', 'vitamin D'),
        (r'\bvitamin c\b', 'vitamin C'),
        (r'\bvitamin e\b', 'vitamin E'),
        # Calcium channel types
        (r'\b(l-type|t-type|n-type|p/q-type)\b', lambda m: m.group(1).upper()),
        # Na+/K+ ATPase
        (r'\bna\+/k\+(\s*)atpase\b', 'Na+/K+-ATPase'),
        (r'\bna\+(\s*)channel\b', 'Na+ channel'),
        (r'\bk\+(\s*)channel\b', 'K+ channel'),
        (r'\bca2\+(\s*)channel\b', 'Ca2+ channel'),
        (r'\bca2\+\b', 'Ca2+'),
        (r'\bmg2\+\b', 'Mg2+'),
        # H2 receptor
        (r'\bh2(\s*)receptor', 'H2 receptor'),
        (r'\bh1(\s*)receptor', 'H1 receptor'),
        # pH
        (r'\bph\s+value\b', 'pH value'),
        (r'\bph\s+gradient\b', 'pH gradient'),
        # Gram-positive/negative
        (r'\bgram-positive\b', 'Gram-positive'),
        (r'\bgram-negative\b', 'Gram-negative'),
        # Parkinson/Alzheimer/Hodgkin
        (r'\bparkinson\'?s\b', "Parkinson's"),
        (r'\balzheimer\'?s\b', "Alzheimer's"),
        (r'\bhuntington\'?s\b', "Huntington's"),
    ]
    for pattern, replacement in fixes:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def fix_my_country(text):
    """Replace 'my country' with 'China'"""
    text = re.sub(r'\bmy country\b', 'China', text)
    text = re.sub(r'\bour country\b', 'China', text)
    return text


def fix_option_casing(text):
    """Fix True/False options: ensure 'True'/'False' not 'Correct'/'Error'"""
    # This handles cases where Google Translate translated option values
    pass  # The retranslate_chapter.py already handles True/False mapping


def fix_microgram(text):
    """Replace 'ug' (microgram) with 'μg' using Greek mu, but NOT in words like 'drug'."""
    # Pattern 1: number + optional space + ug at word boundary
    # e.g., "50 ug", "500ug", "5-10 ug", "0.5-2 ug"
    text = re.sub(r'(\d[\d.]*)\s*ug\b', r'\1 μg', text)
    # Pattern 2: range end (after dash) + ug
    # e.g., "5-10 ug" where "10 ug" is already caught above
    # Pattern 3: ug/unit (e.g., "ug/kg", "ug/ml", "ug/d")
    text = re.sub(r'\bug/(?=[kgmLhd])', 'μg/', text)
    # Pattern 4: ug followed by middle dot (e.g., "ug·kg")
    text = re.sub(r'\bug·', 'μg·', text)
    # Pattern 5: "in ug" or "of ug" (standalone unit reference)
    text = re.sub(r'\b(in|of|about|approximately|around)\s+ug\b', r'\1 μg', text)
    # Pattern 6: ug at end of sentence or before comma
    text = re.sub(r'\bug(\s*[,.;)])', r'μg\1', text)
    return text


def process_csv(in_path, out_path):
    rows = []
    with open(in_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    text_fields = ["question", "explanation", "category"]
    # Also fix option fields for drug names

    for row in rows:
        # Force-standardize True/False question options
        if row.get("type", "").strip() == "True/False":
            row["option_a"] = "True"
            row["option_b"] = "False"
            # Clear any other option fields that may have leaked
            for k in ["option_c", "option_d", "option_e", "option_f",
                       "option_g", "option_h", "option_i", "option_j"]:
                row[k] = ""

        for key in text_fields:
            val = row.get(key, "")
            if not val.strip():
                continue
            val = fix_term_parentheses(val)
            val = fix_full_english_name(val)
            val = fix_drug_capitalization(val)
            val = fix_my_country(val)
            val = fix_microgram(val)
            row[key] = val

        # Fix option text fields too
        for key in sorted(row.keys()):
            if key.startswith("option_"):
                val = row.get(key, "")
                if val.strip():
                    val = fix_drug_capitalization(val)
                    val = fix_my_country(val)
                    val = fix_microgram(val)
                    row[key] = val

    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 postprocess_en.py <input_csv> <output_csv>")
        sys.exit(1)
    n = process_csv(sys.argv[1], sys.argv[2])
    print(f"Processed {n} questions: {sys.argv[1]} -> {sys.argv[2]}")
