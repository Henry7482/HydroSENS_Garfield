from flask import Flask, request, jsonify, send_file
from utils.generate_report import run_generate_report
from utils.helpers import generate_unique_key, generate_unique_file_path, get_json_from_region_csv, save_region_csv
import requests
import os
from flask_cors import CORS  
import zipfile
import tempfile
import os
from werkzeug.datastructures import FileStorage
from io import BytesIO
from data.templates.mock_data import report_data

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
HYDROSENS_STATISTICS = "curve-number, ndvi, precipitation, soil-fraction, temperature, vegetation-fraction"

from utils.coor_convert import lon_to_utm_zone, build_utm_wkt
from pyproj import Transformer
import json

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    
    # TODO: In future versions, use this param to map to different HydroSENS versions
    # statistics = data.get("statistics", "").strip().lower()

    # Prepare data payload
    try:
        data_payload = {
            "region_name": data.get("region_name", "Unknown Region"),
            "start_date": data.get("start_date"),
            "end_date": data.get("end_date"),
            "amc": data.get("amc"),
            "precipitation": data.get("precipitation"),
            "crs": data.get("crs", "EPSG:4326"),
            "num_coordinates": data.get("num_coordinates", 0),
            "coordinates": data.get("coordinates"),
            "endmember": data.get("endmember", 3)  # Extract endmember parameter with default value 3
        }
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid request body."}), 400

    try:
        output_master = os.getenv("OUTPUT_MASTER", "./data/output")
        region_name = data_payload["region_name"]
        start_date = data_payload["start_date"]
        end_date = data_payload["end_date"]
        region_csv_path = os.path.join(output_master, f"{region_name}.csv")
        
        # Check if we already have results for this request
        if os.path.exists(region_csv_path):
            results = get_json_from_region_csv(region_csv_path, start_date, end_date, check_range=True)
            if not results.get("needs_analysis"):
                print(f"[analyze] Found complete results for {region_name} from {start_date} to {end_date}")
                return results
            else:
                prev_outputs = {"outputs": {}}
                prev_outputs["outputs"] = results.get("outputs", {})
                print(f"[analyze] Partial data found. Re-analyzing from {results['analyze_from']} to {end_date}")
                start_date = results["analyze_from"]
                data_payload["start_date"] = start_date  # Update payload with new start date

        # Prepare files payload
        hydrosens_url = os.getenv("HYDROSENS_URL")
        if not hydrosens_url:
            print("[analyze] HYDROSENS_URL not set")
            return jsonify({"error": "HYDROSENS_URL environment variable is not set"}), 500
        hydrosens_url = hydrosens_url.rstrip("/") + "/hydrosens"
        
        print(f"[analyze] Forwarding to HydroSENS at {hydrosens_url}")
        
        # Send request to HydroSENS and wait for the response
        # This will now block until the latest request completes
        response = requests.post(hydrosens_url, json=data_payload, timeout=None)  # No timeout - wait for completion
        print(f"[analyze] HydroSENS responded with status {response.status_code}")

        response_data = response.json()
        return jsonify(response_data), 200
    
    except Exception as e:
        print(f"[analyze] Exception:", str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/analyze/export-tifs', methods=['POST'])
def get_tif_zip():
    """Endpoint to retrieve the zipped TIF output."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400
    
    regionName = data.get("region_name", "Unknown Region")
    startDate = data.get("start_date")
    endDate = data.get("end_date")
    
    if not regionName or not startDate or not endDate:
        return jsonify({"error": "Missing required parameters: region_name, start_date, end_date"}), 400
    
    try:
        # Forward request to HydroSENS API
        hydrosens_url = os.getenv("HYDROSENS_URL")
        if not hydrosens_url:
            print("[get_tif_zip] HYDROSENS_URL not set")
            return jsonify({"error": "HYDROSENS_URL environment variable is not set"}), 500
        
        hydrosens_url = hydrosens_url.rstrip("/") + "/hydrosens/export-tifs"
        
        print(f"[get_tif_zip] Forwarding TIF export request to HydroSENS at {hydrosens_url}")
        
        # Forward the request with date range parameters
        response = requests.get(
            hydrosens_url,
            params={
                "region_name": regionName,
                "start_date": startDate,
                "end_date": endDate
            }
        )
        
        if response.status_code == 200:
            # Create a BytesIO object from the response content
            zip_buffer = BytesIO(response.content)
            
            return send_file(
                zip_buffer,
                mimetype='application/zip',
                as_attachment=True,
                download_name='tif_outputs.zip'
            )
        
        else:
            try:
                error_data = response.json()
                return jsonify(error_data), response.status_code
            except:
                return jsonify({
                    "error": f"HydroSENS TIF export failed with status {response.status_code}"
                }), response.status_code
                
    except Exception as e:
        print(f"[get_tif_zip] Exception: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/analyze/export-csv', methods=['POST'])
def get_csv_file():
    """Endpoint to retrieve the CSV output file."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400
    
    regionName = data.get("region_name", "Unknown Region")
    startDate = data.get("start_date")
    endDate = data.get("end_date")
    
    if not regionName or not startDate or not endDate:
        return jsonify({"error": "Missing required parameters: region_name, start_date, end_date"}), 400
    
    try:
        # Forward request to HydroSENS API
        hydrosens_url = os.getenv("HYDROSENS_URL")
        if not hydrosens_url:
            print("[get_csv_file] HYDROSENS_URL not set")
            return jsonify({"error": "HYDROSENS_URL environment variable is not set"}), 500
        
        hydrosens_url = hydrosens_url.rstrip("/") + "/hydrosens/csv-file"
        
        print(f"[get_csv_file] Forwarding CSV export request to HydroSENS at {hydrosens_url}")
        
        # Forward the request with parameters
        response = requests.get(
            hydrosens_url,
            params={
                "region_name": regionName,
                "start_date": startDate,
                "end_date": endDate
            }
        )
        
        if response.status_code == 200:
            # Create a BytesIO object from the response content
            csv_buffer = BytesIO(response.content)
            
            return send_file(
                csv_buffer,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'{regionName}_output.csv'
            )
        
        else:
            try:
                error_data = response.json()
                return jsonify(error_data), response.status_code
            except:
                return jsonify({
                    "error": f"HydroSENS CSV export failed with status {response.status_code}"
                }), response.status_code
                
    except Exception as e:
        print(f"[get_csv_file] Exception: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/generate-report', methods=['POST'])
def generate_report():
    output_master = os.getenv("OUTPUT_MASTER", "./data/output")
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400
    region_name = data.get("region_name", "Unknown Region")
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    coordinates = data.get("coordinates", [])
    if not region_name or not start_date or not end_date or not coordinates:
        return jsonify({"error": "Missing required parameters"}), 400
    
    # Find cached report data
    pdf_file_path = generate_unique_file_path(region_name, start_date, end_date, extension=".pdf")
    print('Checking for cached report at:', pdf_file_path)
    if os.path.exists(pdf_file_path):
        return send_file(
            pdf_file_path,
            as_attachment=True,
            mimetype='application/pdf',
            download_name='report.pdf'
        )

    report_filename = generate_unique_key(region_name, start_date, end_date)
    csv_file_path = os.path.join(output_master, f"{region_name}.csv")

    if os.path.exists(csv_file_path):
        json_data = get_json_from_region_csv(csv_file_path, start_date, end_date, check_range=False)

    else:
        return jsonify({"error": "CSV file not found or invalid"}), 404
    json_data['region'] = region_name
    json_data['coordinates'] = coordinates
    json_data['time_period'] = {
        "start_date": start_date,
        "end_date": end_date
    }
    try:
        # Run report generation and get the output PDF path
        pdf_file_path = run_generate_report(json_data, report_filename)
        # pdf_file_path = run_generate_report(report_data) # DEMO ONLY

        # Send the file to the user
        return send_file(
            pdf_file_path,
            as_attachment=True,
            mimetype='application/pdf',
            download_name='report.pdf'
        )
    except Exception as e:
        app.logger.error(f"Report generation failed: {str(e)}")
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)