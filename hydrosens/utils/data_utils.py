import os
import pandas as pd
from datetime import datetime, timedelta


def get_dates_from_range(start_date, end_date):
    """Convert date range to list of dates"""
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)
    
    return dates


def check_existing_data(output_master, region_name, requested_dates):
    """
    Check what data already exists in the CSV file and determine which dates need processing.
    
    Returns:
        tuple: (dates_to_process, existing_data_dict)
    """
    csv_file_path = os.path.join(output_master, region_name, 'output.csv')
    
    # Convert requested dates to string format for comparison
    requested_date_strings = [date.strftime('%Y-%m-%d') if isinstance(date, datetime) else date for date in requested_dates]
    
    existing_data = {}
    dates_to_process = requested_date_strings.copy()
    
    if os.path.exists(csv_file_path):
        try:
            df = pd.read_csv(csv_file_path)
            print(f"Found existing CSV with {len(df)} rows")
            
            # Check which requested dates already have complete data OR are marked as NO DATA
            for date_str in requested_date_strings:
                date_rows = df[df['date'] == date_str]
                if len(date_rows) > 0:
                    row = date_rows.iloc[0]
                    
                    # Check if this date is marked as NO DATA
                    if (pd.notna(row.get('veg_mean')) and 
                        str(row.get('veg_mean')).upper() == 'NO DATA'):
                        print(f"Date {date_str} marked as NO DATA, skipping processing")
                        dates_to_process.remove(date_str)
                        # Don't add NO DATA entries to existing_data (they won't be returned to API)
                        continue
                    
                    # Check if the row has all required columns with valid numeric data
                    required_columns = ['veg_mean', 'soil_mean', 'curve_number', 'ndvi', 'temperature', 'precipitation']
                    
                    if all(pd.notna(row.get(col)) and 
                          str(row.get(col)).upper() != 'NO DATA' for col in required_columns):
                        print(f"Date {date_str} already has complete data, skipping processing")
                        existing_data[date_str] = {
                            "ndvi": float(row.get('ndvi', 0)),
                            "soil-fraction": float(row.get('soil_mean', 0)),
                            "vegetation-fraction": float(row.get('veg_mean', 0)),
                            "precipitation": float(row.get('precipitation', 0)),
                            "temperature": float(row.get('temperature', 0)),
                            "curve-number": float(row.get('curve_number', 0))
                        }
                        dates_to_process.remove(date_str)
                    else:
                        print(f"Date {date_str} has incomplete data, will reprocess")
                else:
                    print(f"Date {date_str} not found in existing data, will process")
        except Exception as e:
            print(f"Error reading existing CSV: {e}")
            # If there's an error reading the CSV, process all dates
            pass
    else:
        print(f"No existing CSV found at {csv_file_path}, will process all dates")
    
    # Convert dates_to_process back to datetime objects
    dates_to_process_dt = [datetime.strptime(date_str, '%Y-%m-%d') for date_str in dates_to_process]
    
    print(f"Total requested dates: {len(requested_date_strings)}")
    print(f"Dates with existing data: {len(existing_data)}")
    print(f"Dates to process: {len(dates_to_process_dt)}")
    
    return dates_to_process_dt, existing_data


def append_to_csv(output_master, region_name, new_data, no_data_dates=None):
    """
    Append new data to the CSV file, maintaining chronological order.
    Also marks dates with no data as "NO DATA".
    """
    csv_file_path = os.path.join(output_master, region_name, 'output.csv')
    region_output_dir = os.path.join(output_master, region_name)
    os.makedirs(region_output_dir, exist_ok=True)
    
    # Convert new data to DataFrame format
    new_rows = []
    
    # Add successful processing results
    for date_str, values in new_data.items():
        row = {
            'date': date_str,
            'veg_mean': values.get('vegetation-fraction', 0),
            'soil_mean': values.get('soil-fraction', 0),
            'curve_number': values.get('curve-number', 0),
            'ndvi': values.get('ndvi', 0),
            'temperature': values.get('temperature', 0),
            'precipitation': values.get('precipitation', 0)
        }
        new_rows.append(row)
    
    # Add NO DATA entries for dates with no imagery
    if no_data_dates:
        for date_str in no_data_dates:
            row = {
                'date': date_str,
                'veg_mean': 'NO DATA',
                'soil_mean': 'NO DATA',
                'curve_number': 'NO DATA',
                'ndvi': 'NO DATA',
                'temperature': 'NO DATA',
                'precipitation': 'NO DATA'
            }
            new_rows.append(row)
        print(f"Marking {len(no_data_dates)} dates as NO DATA: {no_data_dates}")
    
    if not new_rows:
        print("No new data to append")
        return csv_file_path
    
    new_df = pd.DataFrame(new_rows)
    new_df = new_df.sort_values('date')
    
    # Check if CSV exists
    if os.path.exists(csv_file_path):
        try:
            # Read existing CSV
            existing_df = pd.read_csv(csv_file_path)
            print(f"Found existing CSV with {len(existing_df)} rows")
            
            # Remove any rows for dates we're updating (in case of reprocessing)
            new_dates = set(new_df['date'].tolist())
            existing_df = existing_df[~existing_df['date'].isin(new_dates)]
            
            # Combine and sort
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df = combined_df.sort_values('date').reset_index(drop=True)
            
            print(f"Appending {len(new_df)} new rows to existing {len(existing_df)} rows")
            
        except Exception as e:
            print(f"Error reading existing CSV: {e}. Creating new file.")
            combined_df = new_df
    else:
        print("Creating new CSV file")
        combined_df = new_df
    
    # Write the combined data
    combined_df.to_csv(csv_file_path, index=False)
    print(f"CSV updated at {csv_file_path} with {len(combined_df)} total rows")
    
    return csv_file_path 