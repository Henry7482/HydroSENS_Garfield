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


@app.route("/analyze", methods=["POST"])
def analyze():
    statistics = request.form.get("statistics", "").strip().lower()
    if statistics != HYDROSENS_STATISTICS:
        return jsonify({"error": "Invalid statistics parameter"}), 400

    # Check if we have individual shapefile components
    shapefile_shp = request.files.get("shapefile_shp")
    shapefile_shx = request.files.get("shapefile_shx")
    shapefile_dbf = request.files.get("shapefile_dbf")
    shapefile_prj = request.files.get("shapefile_prj")
    
    # Check if we have a zipped shapefile
    shapefile_zip = request.files.get("shapefile")

    files_payload = {}
    
    # If we have all 4 individual files, use them directly
    if shapefile_shp and shapefile_shx and shapefile_dbf and shapefile_prj:
        files_payload = {
            "shapefile_shp": shapefile_shp,
            "shapefile_shx": shapefile_shx,
            "shapefile_dbf": shapefile_dbf,
            "shapefile_prj": shapefile_prj,
        }
        print("🔍 [analyze] Using individual shapefile components")
    
    # If we have a zip file, extract it
    elif shapefile_zip:
        try:
            print("🔍 [analyze] Processing zipped shapefile")
            
            # Read the zip file into memory
            zip_data = shapefile_zip.read()
            
            # Extract files from zip
            with zipfile.ZipFile(BytesIO(zip_data), 'r') as zip_ref:
                extracted_files = {}
                
                for file_info in zip_ref.filelist:
                    filename = file_info.filename.lower()
                    
                    # Skip directories and hidden files
                    if file_info.is_dir() or filename.startswith('.'):
                        continue
                    
                    # Extract the file content
                    file_content = zip_ref.read(file_info)
                    
                    # Create FileStorage objects for each shapefile component
                    if filename.endswith('.shp'):
                        extracted_files['shapefile_shp'] = FileStorage(
                            stream=BytesIO(file_content),
                            filename=file_info.filename,
                            content_type='application/octet-stream'
                        )
                    elif filename.endswith('.shx'):
                        extracted_files['shapefile_shx'] = FileStorage(
                            stream=BytesIO(file_content),
                            filename=file_info.filename,
                            content_type='application/octet-stream'
                        )
                    elif filename.endswith('.dbf'):
                        extracted_files['shapefile_dbf'] = FileStorage(
                            stream=BytesIO(file_content),
                            filename=file_info.filename,
                            content_type='application/octet-stream'
                        )
                    elif filename.endswith('.prj'):
                        extracted_files['shapefile_prj'] = FileStorage(
                            stream=BytesIO(file_content),
                            filename=file_info.filename,
                            content_type='application/octet-stream'
                        )
                
                # Check if we have all required components
                required_components = ['shapefile_shp', 'shapefile_shx', 'shapefile_dbf', 'shapefile_prj']
                missing_components = [comp for comp in required_components if comp not in extracted_files]
                
                if missing_components:
                    return jsonify({
                        "error": f"Missing shapefile components in zip: {', '.join(missing_components)}"
                    }), 400
                
                files_payload = extracted_files
                print("✅ [analyze] Successfully extracted shapefile components from zip")
                
        except zipfile.BadZipFile:
            return jsonify({"error": "Invalid zip file"}), 400
        except Exception as e:
            print(f"❌ [analyze] Error processing zip file: {str(e)}")
            return jsonify({"error": f"Error processing zip file: {str(e)}"}), 400
    
    else:
        return jsonify({
            "error": "Either all shapefile components (shp, shx, dbf, prj) or a zipped shapefile is required"
        }), 400

    # Prepare data payload
    data_payload = {
        "start_date": request.form.get("start_date"),
        "end_date": request.form.get("end_date"),
        "amc": request.form.get("amc"),
        "p": request.form.get("p"),
    }

    try:
        print("🔍 [analyze] form data keys:", list(request.form.keys()))
        print("🔍 [analyze] file fields:", list(request.files.keys()))

        hydrosens_url = os.getenv("HYDROSENS_URL")
        if not hydrosens_url:
            print("❌ [analyze] HYDROSENS_URL not set")
            return jsonify({"error": "HYDROSENS_URL environment variable is not set"}), 500
        hydrosens_url = hydrosens_url.rstrip("/") + "/hydrosens"

        print(f"➡️ [analyze] Forwarding to HydroSENS at {hydrosens_url}")
        response = requests.post(hydrosens_url, files=files_payload, data=data_payload)
        print("➡️ [analyze] HydroSENS responded with status", response.status_code)
        print("🔍 [analyze] HydroSENS response body:", response.text)
        return jsonify(response.json()), response.status_code

    except Exception as e:
        print("❌ [analyze] Exception:", str(e))
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