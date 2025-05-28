from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)
HYDROSENS_STATISTICS = "curve-number, ndvi, precipitation, soil-fraction, temperature, vegetation-fraction"

@app.route("/analyze", methods=["POST"])
def analyze():
    # 1. Check required fields
    statistics = request.form.get("statistics", "").strip().lower()
    if statistics == HYDROSENS_STATISTICS:
        # 2. Forward multipart form-data to HydroSENS v1
        shapefile_shp = request.files.get("shapefile_shp")
        shapefile_shx = request.files.get("shapefile_shx")
        shapefile_dbf = request.files.get("shapefile_dbf")
        shapefile_prj = request.files.get("shapefile_prj")

        if not shapefile_shp or not shapefile_shx or not shapefile_dbf or not shapefile_prj :
            return jsonify({"error": "All shapefile components are required"}), 400

        files_payload = {
            "shapefile_shp": shapefile_shp,
            "shapefile_shx": shapefile_shx,
            "shapefile_dbf": shapefile_dbf,
            "shapefile_prj": shapefile_prj,
        }

        data_payload = {
            "start_date": request.form.get("start_date"),
            "end_date": request.form.get("end_date"),
            "amc": request.form.get("amc"),
            "p": request.form.get("p"),
        }

        try:
            # Get the HydroSENS URL
            hydrosens_url = os.getenv("HYDROSENS_URL")
            if not hydrosens_url:
                return jsonify({"error": "HYDROSENS_URL environment variable is not set"}), 500
            response = requests.post(hydrosens_url, files=files_payload, data=data_payload)
            return jsonify(response.json()), response.status_code
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Invalid statistics parameter"}), 400

