from flask import Flask, request, jsonify, send_file
from  utils.generate_report import run_generate_report
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
            hydrosens_url = os.getenv("HYDROSENS_URL") + "/hydrosens"
            if not hydrosens_url:
                return jsonify({"error": "HYDROSENS_URL environment variable is not set"}), 500
            response = requests.post(hydrosens_url, files=files_payload, data=data_payload)
            return jsonify(response.json()), response.status_code
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Invalid statistics parameter"}), 400


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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)