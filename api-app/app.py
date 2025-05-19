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
        shapefile = request.files.get("shapefile")
        if not shapefile:
            return jsonify({"error": "Shapefile is required"}), 400

        files_payload = {
            "shapefile": (shapefile.filename, shapefile.stream, shapefile.content_type)
        }

        data_payload = {
            "startDate": request.form.get("startDate"),
            "endDate": request.form.get("endDate"),
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

