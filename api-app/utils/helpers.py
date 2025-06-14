import hashlib

def generate_unique_key(region_name: str, start_date: str, end_date: str) -> str:
    """
    Generate a unique key based on region name and date range.
    
    Args:
        region_name (str): Name of the region (e.g., "Iowa-Central").
        start_date (str): Start date in format YYYY-MM-DD.
        end_date (str): End date in format YYYY-MM-DD.
        
    Returns:
        str: A unique hash key string.
    """
    base_string = f"{region_name.strip().lower()}_{start_date}_{end_date}"
    unique_key = hashlib.sha256(base_string.encode()).hexdigest()[:12]  # 12-char hash
    return unique_key
