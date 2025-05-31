from flask import Flask, request, jsonify, send_file
from utils.main_sentinel_update import run_hydrosens
import os

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)