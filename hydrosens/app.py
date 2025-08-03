from flask import Flask, request, jsonify, send_file
from utils.main_sentinel_update import run_hydrosens_with_coordinates
from utils.data_utils import get_dates_from_range, check_existing_data, append_to_csv
from utils.thread_utils import terminate_thread
import os
import base64
import json
import zipfile
import tempfile
import threading
import time
import uuid
from datetime import datetime, timedelta
import sys
import pandas as pd

app = Flask(__name__)

# Global variables to track processing state
current_thread = None
current_thread_id = None
current_result = None
result_ready_event = threading.Event()
thread_lock = threading.Lock()


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
    """Endpoint to retrieve the CSV output file with date range filtering."""
    # Get parameters from query string
    region_name = request.args.get('region_name', 'Unknown Region')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Validate required parameters
    if not start_date or not end_date:
        return jsonify({"error": "Missing required parameters: start_date, end_date"}), 400
    
    output_master = os.getenv('OUTPUT_MASTER', '/app/data/output')
    csv_file_path = os.path.join(output_master, region_name, 'output.csv')

    if not os.path.exists(csv_file_path):
        return jsonify({"error": f"CSV output file not found for region '{region_name}'."}), 404

    try:
        import pandas as pd
        from datetime import datetime
        from io import StringIO
        
        # Parse date range
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Read the CSV file
        df = pd.read_csv(csv_file_path)
        
        # Convert date column to datetime for filtering
        df['date'] = pd.to_datetime(df['date'])
        
        # Filter by date range
        filtered_df = df[
            (df['date'] >= start_dt) & 
            (df['date'] <= end_dt)
        ].copy()
        
        # Filter out NO DATA rows
        # Check if any of the main columns contain 'NO DATA'
        no_data_mask = (
            (filtered_df['veg_mean'].astype(str).str.upper() == 'NO DATA') |
            (filtered_df['soil_mean'].astype(str).str.upper() == 'NO DATA') |
            (filtered_df['curve_number'].astype(str).str.upper() == 'NO DATA') |
            (filtered_df['ndvi'].astype(str).str.upper() == 'NO DATA') |
            (filtered_df['temperature'].astype(str).str.upper() == 'NO DATA') |
            (filtered_df['precipitation'].astype(str).str.upper() == 'NO DATA')
        )
        
        # Keep only rows that don't have NO DATA
        filtered_df = filtered_df[~no_data_mask]
        
        # Convert date back to string format for CSV output
        filtered_df['date'] = filtered_df['date'].dt.strftime('%Y-%m-%d')
        
        # Sort by date
        filtered_df = filtered_df.sort_values('date')
        
        print(f"CSV export for region '{region_name}': {len(filtered_df)} rows in date range {start_date} to {end_date} (NO DATA rows excluded)")
        
        if filtered_df.empty:
            return jsonify({
                "error": f"No valid data found for region '{region_name}' in date range {start_date} to {end_date}"
            }), 404
        
        # Create CSV content in memory
        csv_buffer = StringIO()
        filtered_df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()
        
        # Convert to BytesIO for send_file
        from io import BytesIO
        csv_bytes = BytesIO(csv_content.encode('utf-8'))
        
        return send_file(
            csv_bytes,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'{region_name}_{start_date}_to_{end_date}_output.csv'
        )

    except ValueError as e:
        return jsonify({
            "error": f"Invalid date format. Expected YYYY-MM-DD. Error: {str(e)}"
        }), 400
    except Exception as e:
        app.logger.error(f"Error processing CSV file: {str(e)}")
        return jsonify({"error": f"Failed to process CSV file: {str(e)}"}), 500

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