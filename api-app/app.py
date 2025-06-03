from flask import Flask, request, jsonify, send_file
from  utils.generate_report import run_generate_report
import requests
import os
from flask_cors import CORS  
import zipfile
import tempfile
import os
from werkzeug.datastructures import FileStorage
from io import BytesIO

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
        return jsonify(response.json()), response.status_code

    except Exception as e:
        print(f"[analyze] Exception:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/generate-report', methods=['POST'])
def generate_report():
    try:
        # Run report generation and get the output PDF path
        pdf_file_path = run_generate_report(request.get_json())

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

@app.route('/latest-tifs', methods=['GET'])
def latest_tifs():
    # 1. Check required fields
    statistics = request.form.get("statistics", "").strip().lower()
    if statistics == HYDROSENS_STATISTICS:
        try:
            # Get the HydroSENS URL
            hydrosens_url = os.getenv("HYDROSENS_URL") + "/export-latest-tifs"
            if not hydrosens_url:
                return jsonify({"error": "HYDROSENS_URL environment variable is not set"}), 500
            response = requests.get(hydrosens_url)
            if response.status_code != 200:
                return jsonify({"error": "Failed to fetch latest .tif files"}), response.status_code
            return jsonify(response.json()), response.status_code
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Invalid statistics parameter"}), 400

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