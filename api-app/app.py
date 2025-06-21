from flask import Flask, request, jsonify, send_file
from  utils.generate_report import run_generate_report
from utils.helpers import generate_unique_key, generate_unique_file_path, get_json_from_csv
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

import zipfile
import tempfile
import os
from werkzeug.datastructures import FileStorage
from io import BytesIO

from utils.coor_convert import lon_to_utm_zone, build_utm_wkt
from pyproj import Transformer
import json

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400
    statistics = data.get("statistics", "").strip().lower()
    if statistics != HYDROSENS_STATISTICS:
        return jsonify({"error": "Invalid statistics parameter"}), 400

    # Prepare data payload
    try:
        coordinates = data.get("coordinates")
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid coordinates format. Must be a valid JSON array."}), 400

    data_payload = {
        "region_name": data.get("region_name", "Unknown Region"),
        "start_date": data.get("start_date"),
        "end_date": data.get("end_date"),
        "amc": data.get("amc"),
        "precipitation": data.get("precipitation"),
        "crs": data.get("crs", "EPSG:4326"),
        "num_coordinates": data.get("num_coordinates", 0),
        "coordinates": coordinates
    }

    try:
        # Prepare files payload
        hydrosens_url = os.getenv("HYDROSENS_URL")
        if not hydrosens_url:
            print("[analyze] HYDROSENS_URL not set")
            return jsonify({"error": "HYDROSENS_URL environment variable is not set"}), 500
        hydrosens_url = hydrosens_url.rstrip("/") + "/hydrosens"

        print(f"[analyze] Forwarding to HydroSENS at {hydrosens_url}")
        response = requests.post(hydrosens_url, json=data_payload)
        print(f"[analyze] HydroSENS responded with status {response.status_code}")

        output_master = os.getenv("OUTPUT_MASTER", "./data/output")
        filename = generate_unique_key(
                data_payload["region_name"],
                data_payload["start_date"],
                data_payload["end_date"]
        )
        csv_file = requests.get(hydrosens_url + "/csv-file")
        # Save the CSV file to output master
        # Check if download is successful
        if csv_file.status_code == 200:
            # Determine the filename (you can also parse from headers if needed)
            csv_filename = filename + ".csv"
            csv_path = os.path.join(output_master, csv_filename)

            os.makedirs(output_master, exist_ok=True)

            # Write the content to file
            with open(csv_path, "wb") as f:
                f.write(csv_file.content)
                
        # Download zipped TIFs
        tif_zip = requests.get(hydrosens_url + "/export-latest-tifs")
        if tif_zip.status_code == 200:
            tif_zip_filename = filename + ".zip"
            tif_zip_path = os.path.join(output_master, tif_zip_filename)
            with open(tif_zip_path, "wb") as f:
                f.write(tif_zip.content)
            print(f"[analyze] TIF zip saved at: {tif_zip_path}")
        else:
            print(f"[analyze] TIF zip request failed with status {tif_zip.status_code}")

        return jsonify(response.json()), response.status_code

    except Exception as e:
        print(f"[analyze] Exception:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/analyze/export-tifs', methods=['GET'])
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

    zip_file_path = generate_unique_file_path(regionName, startDate, endDate, extension=".zip")
    if not os.path.exists(zip_file_path):
        return jsonify({"error": "TIF ZIP file not found."}), 404

    return send_file(zip_file_path, mimetype='application/zip', as_attachment=True, download_name='tif_outputs.zip')

@app.route('/analyze/export-csv', methods=['GET'])
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
    csv_file_path = generate_unique_file_path(regionName, startDate, endDate, extension=".csv")

    if not os.path.exists(csv_file_path):
        return jsonify({"error": "CSV output file not found."}), 404

    return send_file(csv_file_path, mimetype='text/csv', as_attachment=True, download_name='output.csv')

@app.route('/generate-report', methods=['POST'])
def generate_report():
    # data = request.get_json()
    # if not data:
    #     return jsonify({"error": "Invalid JSON payload"}), 400
    # regionName = data.get("region_name", "Unknown Region")
    # startDate = data.get("start_date")
    # endDate = data.get("end_date")
    # coordinates = data.get("coordinates", [])
    # if not regionName or not startDate or not endDate or not coordinates:
    #     return jsonify({"error": "Missing required parameters"}), 400
    # csv_file_path = generate_unique_file_path(regionName, startDate, endDate, extension=".csv")
    # json_data = get_json_from_csv(csv_file_path)
    # if not json_data:
    #     return jsonify({"error": "CSV file not found or invalid"}), 404
    # json_data['region'] = regionName
    # print(json_data)
    
    try:
        # Run report generation and get the output PDF path
        # pdf_file_path = run_generate_report(json_data)
        pdf_file_path = run_generate_report(report_data)

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

   
@app.route('/convert', methods=['POST'])
def convert_coordinates():
    data = request.get_json()
    
    coordinates = data.get("coordinates")
    if not isinstance(coordinates, list) or not all(isinstance(p, list) and len(p) == 2 for p in coordinates):
        return jsonify(error="Request must include a 'coordinates' field with an array of [lat, lon] pairs."), 400

    results = []
    for lat, lon in coordinates:
        try:
            zone = lon_to_utm_zone(lon)
            is_northern = lat >= 0
            epsg_code = 32600 + zone if is_northern else 32700 + zone
            transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg_code}", always_xy=True)
            x, y = transformer.transform(lon, lat)
            wkt = build_utm_wkt(zone, is_northern)

            results.append({
                "input": {"lat": lat, "lon": lon},
                "utm": {
                    "zone": zone,
                    "epsg": epsg_code,
                    "x": round(x, 3),
                    "y": round(y, 3),
                    "wkt": wkt
                }
            })
        except Exception as e:
            results.append({
                "input": {"lat": lat, "lon": lon},
                "error": f"Projection failed: {str(e)}"
            })

    return jsonify(results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)