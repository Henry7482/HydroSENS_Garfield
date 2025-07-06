import hashlib
import os
import csv

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


def generate_unique_file_path(region_name: str, start_date: str, end_date: str, extension: str = ".csv") -> str:
    """
    Generate a unique filename based on region name and date range.
    Args:
        region_name (str): Name of the region (e.g., "Iowa-Central").
        start_date (str): Start date in format YYYY-MM-DD.
        end_date (str): End date in format YYYY-MM-DD.
        extension (str): File extension, default is ".csv".
    Returns:
        str: Full file path with unique filename.
    """
    fileName = generate_unique_key(region_name, start_date, end_date) + extension
    if (extension == ".pdf"):
        outputMaster = './data/generated_reports'
    else:
        outputMaster = os.getenv('OUTPUT_MASTER', './data/output')
    filePath = os.path.join(outputMaster, fileName)
    return filePath

def get_json_from_csv(csv_path: str) -> dict:
    """
    Convert a CSV file to a JSON object.
    
    Args:
        csv_file_path (str): Path to the CSV file.
        
    Returns:
        dict: JSON representation of the CSV data.
    """
    output = {"outputs": {}}

    with open(csv_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            date = row["date"]
            veg = float(row["veg_mean"])
            soil = float(row["soil_mean"])

            output["outputs"][date] = {
                "curve-number": float(row["curve_number"]),
                "ndvi": float(row["ndvi"]),
                "precipitation": float(row["precipitation"]),
                "soil-fraction": soil,
                "temperature": float(row["temperature"]),
                "vegetation-fraction": veg,
            }
    return output