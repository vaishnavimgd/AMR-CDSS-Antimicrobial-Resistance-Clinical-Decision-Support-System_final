"""
Outbreak Alert System for AMR-CDSS.
Logs prediction cases and detects outbreaks (e.g. 3+ cases of the same rare resistance profile in 7 days in a ward).
"""
from datetime import datetime, timedelta
from typing import List, Dict

# In-memory dictionary logging cases
# Format: list of dicts {ward: str, species: str, resistance_profile: list, timestamp: datetime}
OUTBREAK_LOG: List[Dict] = []

def log_case(ward: str, species: str, resistance_profile: list):
    """
    Log a case for outbreak tracking.
    """
    # Ensure resistance_profile is sorted strings or simplified for easy matching
    safe_profile = sorted(list(resistance_profile))
    
    case_data = {
        "ward": ward,
        "species": species,
        "resistance_profile": safe_profile,
        "timestamp": datetime.now()
    }
    OUTBREAK_LOG.append(case_data)

def check_outbreak(ward: str, resistance_profile: list) -> dict | None:
    """
    Check if the given ward and resistance profile triggers an outbreak alert.
    Condition: 3 or more times within a 7-day rolling window for the same ward.
    """
    if not resistance_profile:
        return None
        
    safe_profile = sorted(list(resistance_profile))
    
    # Needs to be a concerning profile. We'll alert if *any* resistant genes are detected
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    # Count matching cases in the last 7 days
    count = 0
    for case in OUTBREAK_LOG:
        if case["ward"] == ward and case["resistance_profile"] == safe_profile and case["timestamp"] >= seven_days_ago:
            count += 1
            
    if count >= 3:
        return {
            "ward": ward,
            "strain": ", ".join(safe_profile),
            "case_count": count,
            "days_window": 7,
            "severity": "High"
        }
    return None

def species_name(sp: str) -> str:
    mapping = {
        "ecoli": "Escherichia coli",
        "saureus": "Staphylococcus aureus",
        "cdiff": "Clostridioides difficile"
    }
    return mapping.get(sp, sp)

def get_all_alerts() -> list:
    """
    Returns a list of all current active alerts across all wards and profiles.
    """
    alerts = []
    checked = set()
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    # Consider only recent logs
    recent_logs = [c for c in OUTBREAK_LOG if c["timestamp"] >= seven_days_ago]
    
    for case in recent_logs:
        profile_tuple = tuple(case["resistance_profile"])
        if not profile_tuple:
            continue
            
        key = (case["ward"], case["species"], profile_tuple)
        if key in checked:
            continue
            
        checked.add(key)
        
        # Count occurrences
        count = sum(1 for c in recent_logs if c["ward"] == key[0] and c["species"] == key[1] and tuple(c["resistance_profile"]) == key[2])
        if count >= 3:
            alerts.append({
                "ward": key[0],
                "strain": f"{species_name(key[1])} [{' + '.join(key[2])}]",
                "case_count": count,
                "days_window": 7,
                "severity": "High"
            })
            
    return alerts
