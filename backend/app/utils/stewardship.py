"""
Antibiotic Stewardship Recommender.
Returns WHO AWaRe guideline recommendations based on species and resistance profile.
"""

def get_recommendation(species: str, resistance_profile: list) -> dict:
    """
    Returns antibiotic recommendations based on WHO AWaRe guidelines.
    """
    profile_set = set(r.lower() for r in resistance_profile)
    sp = species.lower()

    # Rule 1
    if sp in ["ecoli", "escherichia coli"] and "ndm-1" in profile_set:
        return {
            "avoid": ["All Carbapenems", "All Penicillins"],
            "recommend": ["Colistin", "Fosfomycin"],
            "category": "Reserve",
            "warning": "Last-resort agents only. Contact infectious disease specialist."
        }
        
    # Rule 2
    if sp in ["ecoli", "escherichia coli"] and "extended-spectrum beta-lactamase" in profile_set:
        return {
            "avoid": ["Cephalosporins", "Penicillins"],
            "recommend": ["Meropenem", "Nitrofurantoin"],
            "category": "Watch",
            "warning": ""
        }

    # Rule 3
    if sp in ["ecoli", "escherichia coli"] and "blatem-1" in profile_set:
        return {
            "avoid": ["Ampicillin"],
            "recommend": ["Nitrofurantoin", "Fosfomycin", "Ceftriaxone"],
            "category": "Access",
            "warning": ""
        }
        
    # Rule 4
    if sp in ["saureus", "staphylococcus aureus"] and "meca" in profile_set:
        return {
            "avoid": ["All Beta-lactams", "Methicillin"],
            "recommend": ["Vancomycin", "Linezolid"],
            "category": "Watch",
            "warning": "MRSA detected. Standard beta-lactams are ineffective."
        }

    # Rule 5
    if sp in ["saureus", "staphylococcus aureus"] and "vancomycin" in profile_set:
        return {
            "avoid": ["Vancomycin", "Beta-lactams"],
            "recommend": ["Linezolid", "Daptomycin"],
            "category": "Reserve",
            "warning": "VRSA detected. Highly restricted options."
        }

    # Rule 6
    if sp in ["cdiff", "clostridioides difficile"] and ("fluoroquinolones" in profile_set or "ciprofloxacin" in profile_set):
        return {
            "avoid": ["Fluoroquinolones", "Clindamycin", "Cephalosporins"],
            "recommend": ["Vancomycin (oral)", "Fidaxomicin"],
            "category": "Watch",
            "warning": "Ensure oral formulation for Vancomycin."
        }
        
    # Rule 7
    if sp in ["ecoli", "escherichia coli"] and "tetracycline" in profile_set:
        return {
            "avoid": ["Tetracycline", "Doxycycline"],
            "recommend": ["Trimethoprim/Sulfamethoxazole", "Nitrofurantoin"],
            "category": "Access",
            "warning": ""
        }
        
    # Rule 8
    if sp in ["saureus", "staphylococcus aureus"] and "erythromycin" in profile_set:
        return {
            "avoid": ["Macrolides", "Erythromycin"],
            "recommend": ["Clindamycin (if D-test negative)", "Trimethoprim/Sulfamethoxazole"],
            "category": "Watch",
            "warning": "Check for inducible clindamycin resistance."
        }
        
    # Rule 9
    if "colistin" in profile_set:
        return {
            "avoid": ["Colistin"],
            "recommend": ["Tigecycline", "Ceftazidime/Avibactam"],
            "category": "Reserve",
            "warning": "Pan-drug resistance risk. Extreme caution required."
        }

    # Rule 10 (Default / Wild-type)
    if sp in ["ecoli", "escherichia coli"]:
        return {
            "avoid": [],
            "recommend": ["Ampicillin", "Amoxicillin", "Nitrofurantoin"],
            "category": "Access",
            "warning": ""
        }
        
    if sp in ["saureus", "staphylococcus aureus"]:
        return {
            "avoid": [],
            "recommend": ["Oxacillin", "Cefazolin"],
            "category": "Access",
            "warning": ""
        }
        
    if sp in ["cdiff", "clostridioides difficile"]:
        return {
            "avoid": ["Clindamycin", "Fluoroquinolones"],
            "recommend": ["Vancomycin (oral)", "Fidaxomicin"],
            "category": "Watch",
            "warning": ""
        }

    # Catch-all
    return {
        "avoid": [],
        "recommend": ["Consult local antibiogram"],
        "category": "Access",
        "warning": "Unrecognized profile."
    }
