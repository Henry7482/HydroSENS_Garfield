from flask import Flask, request, jsonify, send_file
from utils.main_sentinel_update import run_hydrosens_with_coordinates
import os
import base64
import json
import zipfile
import tempfile
import threading
import time
import uuid
from datetime import datetime, timedelta
import ctypes
import sys
import pandas as pd

app = Flask(__name__)

# Global variables to track processing state
current_thread = None
current_thread_id = None
current_result = None
result_ready_event = threading.Event()
thread_lock = threading.Lock()

def terminate_thread(thread):
    """Terminate a thread forcefully"""
    if not thread or not thread.is_alive():
        return
    
    try:
        # Get the thread ID
        thread_id = thread.ident
        if thread_id is None:
            return
            
        # Force terminate the thread
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(thread_id), 
            ctypes.py_object(SystemExit)
        )
        
        if res == 0:
            print("Failed to terminate thread - invalid thread ID")
        elif res != 1:
            # If it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, None)
            print("Exception raise failure")
        else:
            print(f"Thread {thread_id} terminated successfully")
            
    except Exception as e:
        print(f"Error terminating thread: {str(e)}")

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

def run_hydrosens_background(thread_id, region_name, coordinates, start_date, end_date, output_dir, amc, precipitation, crs, endmember):
    """
    Wrapper function that runs hydrosens analysis in background with caching
    """
    global current_result
    
    try:
        print(f"Starting Hydrosens analysis (Thread: {thread_id}) for region: {region_name}")
        
        # Step 1: Get all dates in the requested range
        requested_dates = get_dates_from_range(start_date, end_date)
        print(f"Requested date range: {start_date} to {end_date} ({len(requested_dates)} dates)")
        
        # Step 2 & 3: Check existing data and determine what needs processing
        dates_to_process, existing_data = check_existing_data(output_dir, region_name, requested_dates)
        
        if len(dates_to_process) == 0:
            print("All requested dates already have complete data, no processing needed")
            current_result = {
                'success': True,
                'message': 'All data already available from cache',
                'parameters': {
                    'region_name': region_name,
                    'start_date': start_date,
                    'end_date': end_date,
                    'amc': amc,
                    'precipitation': precipitation,
                    'coordinates': coordinates,
                    'crs': crs,
                    'endmember': endmember,
                    'num_coordinates': len(coordinates),
                    'dates_from_cache': len(existing_data),
                    'dates_processed': 0
                },
                'outputs': existing_data
            }
        else:
            # Step 4: Run hydrosens on the dates that have no data
            print(f"Processing {len(dates_to_process)} dates that need analysis")
            new_results = run_hydrosens_with_coordinates(
                region_name=region_name,
                coordinates=coordinates,
                dates_to_process=dates_to_process,  # Pass specific dates instead of range
                output_dir=output_dir,
                amc=amc,
                precipitation=precipitation,
                crs=crs,
                endmember=endmember
            )
            
            # Step 5: Determine which dates had no data (were requested but not in results)
            processed_date_strings = set(new_results.keys())
            requested_date_strings = set(date.strftime('%Y-%m-%d') for date in dates_to_process)
            no_data_dates = list(requested_date_strings - processed_date_strings)
            
            if no_data_dates:
                print(f"Found {len(no_data_dates)} dates with no Sentinel-2 imagery available")
            
            # Step 6: Append the new results to the CSV file, including NO DATA markers
            csv_path = append_to_csv(output_dir, region_name, new_results, no_data_dates)
            
            # Step 7: Return combined result (excluding NO DATA entries)
            combined_results = {**existing_data, **new_results}
            
            current_result = {
                'success': True,
                'message': 'Hydrosens analysis completed successfully',
                'parameters': {
                    'region_name': region_name,
                    'start_date': start_date,
                    'end_date': end_date,
                    'amc': amc,
                    'precipitation': precipitation,
                    'coordinates': coordinates,
                    'crs': crs,
                    'endmember': endmember,
                    'num_coordinates': len(coordinates),
                    'dates_from_cache': len(existing_data),
                    'dates_processed': len(new_results),
                    'dates_no_data': len(no_data_dates)
                },
                'outputs': combined_results
            }
        
        print(f"Thread {thread_id} completed successfully for region: {region_name}")
        result_ready_event.set()
        
    except SystemExit:
        # Thread was terminated
        print(f"Thread {thread_id} was terminated")
        return
        
    except Exception as e:
        print(f"Thread {thread_id} failed: {str(e)}")
        current_result = {
            'success': False,
            'error': str(e)
        }
        result_ready_event.set()

@app.route('/hydrosens', methods=['POST'])
def run_hydrosens_endpoint():
    """
    Endpoint that starts background processing and waits for the latest result
    """
    global current_thread, current_thread_id, current_result
    
    output_master = os.getenv('OUTPUT_MASTER', '/app/data/output')
    
    try:
        data = request.get_json()
        
        # Extract parameters
        region_name = data.get('region_name', 'Unknown Region')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        amc = data.get('amc')
        precipitation = data.get('precipitation') or data.get('p')
        coordinates = data.get('coordinates')
        crs = data.get('crs', 'EPSG:4326')
        endmember = data.get('endmember')  # Extract endmember parameter
        
        # Validate required parameters
        if not all([start_date, end_date, coordinates]):
            missing = []
            if not start_date: missing.append('start_date')
            if not end_date: missing.append('end_date') 
            if not amc: missing.append('amc')
            if not precipitation: missing.append('precipitation')
            if not coordinates: missing.append('coordinates')
            if not crs: missing.append('crs')
            if not endmember: missing.append('endmember')
            return jsonify({
                "error": f"Missing required parameters: {', '.join(missing)}"
            }), 400
        
        # Create output directory
        os.makedirs(output_master, exist_ok=True)
        
        # Thread management
        with thread_lock:
            # Generate new thread ID
            new_thread_id = str(uuid.uuid4())
            
            # Terminate current thread if it exists
            if current_thread and current_thread.is_alive():
                print(f"Terminating existing thread: {current_thread_id}")
                terminate_thread(current_thread)
                
                # Give it a moment to clean up
                time.sleep(0.1)
            
            # Reset result state
            current_result = None
            result_ready_event.clear()
            
            # Create and start new thread with region_name and endmember parameter
            current_thread = threading.Thread(
                target=run_hydrosens_background,
                args=(new_thread_id, region_name, coordinates, start_date, end_date, output_master, amc, precipitation, crs, endmember)
            )
            current_thread_id = new_thread_id
            current_thread.start()
        
        # Log the request parameters
        print(f"Started Hydrosens analysis (Thread: {new_thread_id}) for region: {region_name}:")
        app.logger.info(f"  Date range: {start_date} to {end_date}")
        app.logger.info(f"  AMC: {amc}, Precipitation: {precipitation}mm")
        app.logger.info(f"  Endmembers: {endmember} ({'vegetation, soil' if endmember == 2 else 'vegetation, impervious, soil'})")
        app.logger.info(f"  Coordinates: {len(coordinates)} points, CRS: {crs}")
        app.logger.info(f"  Output directory: {output_master}")
        
        # Wait for the result (this blocks until processing is complete or cancelled)
        print(f"Waiting for thread {new_thread_id} to complete...")
        result_ready_event.wait()
        
        # Check if this thread was superseded (another request came in)
        if current_thread_id != new_thread_id:
            print(f"Thread {new_thread_id} was superseded by {current_thread_id}")
            return jsonify({}), 200  # Conflict
        
        # Return the result
        if current_result and current_result.get('success'):
            print(f"Thread {new_thread_id} completed successfully")
            return jsonify(current_result), 200
        else:
            error_msg = current_result.get('error', 'Unknown error') if current_result else 'No result available'
            print(f"Thread {new_thread_id} failed: {error_msg}")
            return jsonify({
                "error": error_msg
            }), 500
        
    except Exception as e:
        app.logger.error(f"Error in Hydrosens analysis: {str(e)}")
        return jsonify({
            "error": f"Analysis failed: {str(e)}"
        }), 500

@app.route('/hydrosens/csv-file', methods=['GET'])
def get_csv_file():
    """Endpoint to retrieve the CSV output file."""
    # Get region_name from query parameters
    region_name = request.args.get('region_name', 'Unknown Region')
    
    output_master = os.getenv('OUTPUT_MASTER', '/app/data/output')
    # Update path to include region folder
    csv_file_path = os.path.join(output_master, region_name, 'output.csv')

    if not os.path.exists(csv_file_path):
        return jsonify({"error": "CSV output file not found."}), 404

    return send_file(csv_file_path, mimetype='text/csv', as_attachment=True, download_name='output.csv')


@app.route('/hydrosens/export-tifs', methods=['GET'])
def export_tifs_zip():
    """Create and return a zip of .tif files within the specified date range."""
    import zipfile
    from io import BytesIO
    from datetime import datetime

    # Get date range parameters and region name
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    region_name = request.args.get('region_name', 'Unknown Region')
    
    if not start_date or not end_date:
        return jsonify({"error": "Missing required parameters: start_date, end_date"}), 400

    output_master = os.getenv('OUTPUT_MASTER', '/app/data/output')
    # Update path to include region folder
    region_output_dir = os.path.join(output_master, region_name)
    zip_buffer = BytesIO()

    if not os.path.exists(region_output_dir):
        return jsonify({"error": f"Output folder for region '{region_name}' does not exist"}), 404

    try:
        # Parse date range for filtering
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        tif_files_found = False
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for date_folder in os.listdir(region_output_dir):
                date_path = os.path.join(region_output_dir, date_folder)
                
                # Skip if not a directory
                if not os.path.isdir(date_path):
                    continue
                
                try:
                    # Parse folder name as date (assuming YYYY-MM-DD format)
                    folder_dt = datetime.strptime(date_folder, '%Y-%m-%d')
                    
                    # Check if folder date is within the specified range
                    if start_dt <= folder_dt <= end_dt:
                        print(f"Including date folder: {date_folder}")
                        
                        # Add all .tif files from this date folder
                        for file_name in os.listdir(date_path):
                            if file_name.endswith('.tif'):
                                file_path = os.path.join(date_path, file_name)
                                arcname = os.path.join(date_folder, file_name)
                                zipf.write(file_path, arcname=arcname)
                                tif_files_found = True
                                print(f"Added to zip: {arcname}")
                    else:
                        print(f"Skipping date folder outside range: {date_folder}")
                        
                except ValueError:
                    # Skip folders that don't match date format
                    print(f"Skipping non-date folder: {date_folder}")
                    continue

        if not tif_files_found:
            return jsonify({
                "error": f"No TIF files found for region '{region_name}' in date range {start_date} to {end_date}"
            }), 404

        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'tif_outputs_{region_name}_{start_date}_to_{end_date}.zip'
        )

    except ValueError as e:
        return jsonify({
            "error": f"Invalid date format. Expected YYYY-MM-DD. Error: {str(e)}"
        }), 400
    except Exception as e:
        app.logger.error(f"Error creating TIF zip: {str(e)}")
        return jsonify({"error": f"Failed to create TIF zip: {str(e)}"}), 500
    
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    app.run(host="0.0.0.0", port=5050, debug=True)