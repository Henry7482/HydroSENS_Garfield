from flask import Flask, request, jsonify, send_file
from utils.main_sentinel_update import run_hydrosens
import os
import base64

app = Flask(__name__)

@app.route('/hydrosens', methods=['POST'])
def run_hydrosens_endpoint():
    output_master = os.getenv('OUTPUT_MASTER')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    amc = request.form.get('amc')
    p = request.form.get('p')
    # Get uploaded shapefile components
    shapefile_parts = {
        'shp': request.files.get('shapefile_shp'),
        'shx': request.files.get('shapefile_shx'),
        'dbf': request.files.get('shapefile_dbf'),
        'prj': request.files.get('shapefile_prj'),
    }

    if not output_master or not start_date or not end_date:
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        amc = int(amc) if amc else None
        p = int(p) if p else None

        # Create the target directory inside the Docker volume
        shapefiles_path = '/app/data/shape'
        os.makedirs(shapefiles_path, exist_ok=True)

        # Save the uploaded files into the volume
        shapefile_base = 'input_shapefile'  # name without extension
        for ext, file in shapefile_parts.items():
            if file:
                save_path = os.path.join(shapefiles_path, f'{shapefile_base}.{ext}')
                file.save(save_path)

        data = run_hydrosens(output_master, start_date, end_date, output_master, amc, p, shapefiles_path)
        result = {"message": "Hydrosens run completed successfully", "outputs": data}
        print("Data:", data)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/export-latest-tifs', methods=['GET'])
def export_tifs_content():
    output_master = "/app/data/output"
    tif_by_date = {}

    if not os.path.exists(output_master):
        return jsonify({"error": "Output folder does not exist"}), 404

    for date_folder in os.listdir(output_master):
        date_path = os.path.join(output_master, date_folder)
        if os.path.isdir(date_path):
            date_tifs = {}
            for f in os.listdir(date_path):
                if f.endswith('.tif'):
                    file_path = os.path.join(date_path, f)
                    try:
                        with open(file_path, 'rb') as file:
                            encoded = base64.b64encode(file.read()).decode('utf-8')
                            date_tifs[f] = encoded
                    except Exception as e:
                        date_tifs[f] = f"Error reading file: {str(e)}"
            if date_tifs:
                tif_by_date[date_folder] = date_tifs

    return jsonify({
        "message": "Exported .tif file contents as base64",
        "tif_files": tif_by_date
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)