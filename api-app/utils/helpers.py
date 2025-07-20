import hashlib
import os
import csv
from datetime import datetime


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

from datetime import datetime, timedelta

def get_json_from_region_csv(csv_path: str, start_date: str, end_date: str, check_range: bool) -> dict | None:
    """
    Read a region-based CSV and return filtered JSON data by date range.
    If the end_date is missing, return a signal to re-analyze from the last available date + 1.

    Returns:
        dict with:
            - 'outputs': filtered data
            - 'needs_analysis': bool
            - 'analyze_from': optional start date if analysis is needed
    """
    output = {"outputs": {}}
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            row_date = datetime.strptime(row["date"], "%Y-%m-%d")
            if start_dt <= row_date <= end_dt:
                output["outputs"][row["date"]] = {
                    "curve-number": float(row["curve_number"]),
                    "ndvi": float(row["ndvi"]),
                    "precipitation": float(row["precipitation"]),
                    "soil-fraction": float(row["soil_mean"]),
                    "temperature": float(row["temperature"]),
                    "vegetation-fraction": float(row["veg_mean"]),
                }

    if not check_range:
        return {
            "outputs": output["outputs"],
            "needs_analysis": False
        }
    # Check if end_date is missing
    expected_dates = get_expected_dates(start_date, end_date)
    missing_dates = [d for d in expected_dates if d not in output["outputs"]]

    if not output["outputs"]:
        return {
            "needs_analysis": True,
            "analyze_from": start_date
        }

    if missing_dates:
        # If only tail is missing
        last_available_date = max(datetime.strptime(d, "%Y-%m-%d") for d in output["outputs"])
        next_date = (last_available_date + timedelta(days=1)).strftime("%Y-%m-%d")
        return {
            "outputs": output["outputs"],
            "needs_analysis": True,
            "analyze_from": next_date
        }

    return {
        "outputs": output["outputs"],
        "needs_analysis": False
    }


def get_expected_dates(start_date: str, end_date: str) -> list:
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    return [(start_dt + timedelta(days=i)).strftime("%Y-%m-%d") 
            for i in range((end_dt - start_dt).days + 1)]


def save_region_csv(region_name: str, csv_bytes: bytes, output_dir: str):
    """
    Saves CSV data to a file based on region name.
    If the file exists, it appends only new entries by date.
    """
    region_csv_path = os.path.join(output_dir, f"{region_name}.csv")

    # Decode and parse downloaded CSV
    csv_content = csv_bytes.decode("utf-8").splitlines()
    reader = csv.DictReader(csv_content)

    # Track dates already in file (if exists)
    existing_dates = set()
    file_exists = os.path.exists(region_csv_path)

    if file_exists:
        with open(region_csv_path, mode="r", newline="", encoding="utf-8") as f:
            existing_reader = csv.DictReader(f)
            for row in existing_reader:
                existing_dates.add(row["date"])

    # Append new data
    with open(region_csv_path, mode="a" if file_exists else "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=reader.fieldnames)

        # Write header if creating new file
        if not file_exists:
            writer.writeheader()

        new_lines_added = 0
        for row in reader:
            if row["date"] not in existing_dates:
                writer.writerow(row)
                new_lines_added += 1

    print(f"[analyze] Updated {region_csv_path} with {new_lines_added} new entries.")