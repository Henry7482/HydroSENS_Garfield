from flask import Flask, request, jsonify, send_file
from utils.main_sentinel_update import run_hydrosens_with_coordinates
import os
import base64
import json

app = Flask(__name__)

@app.route('/hydrosens', methods=['POST'])
def run_hydrosens_endpoint():
    """
    Updated endpoint that accepts coordinates instead of shapefiles.
    
    Expected JSON payload:
    {
        "start_date": "2023-06-01",
        "end_date": "2023-06-30", 
        "amc": 2,
        "precipitation": 10.5,
        "coordinates": [
            [-120.5, 36.2],
            [-120.4, 36.2], 
            [-120.4, 36.3],
            [-120.5, 36.3]
        ],
        "crs": "EPSG:4326"
    }
    """
    output_master = os.getenv('OUTPUT_MASTER', '/app/data/output')
    
    try:
        # Parse JSON data from request
        if request.is_json:
            data = request.get_json()
        else:
            # Fallback to form data for backward compatibility
            data = {
                'start_date': request.form.get('start_date'),
                'end_date': request.form.get('end_date'),
                'amc': request.form.get('amc'),
                'precipitation': request.form.get('p') or request.form.get('precipitation'),
                'coordinates': json.loads(request.form.get('coordinates', '[]')),
                'crs': request.form.get('crs', 'EPSG:4326')
            }
        
        # Extract parameters
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        amc = data.get('amc')
        precipitation = data.get('precipitation') or data.get('p')  # Support both field names
        coordinates = data.get('coordinates')
        crs = data.get('crs', 'EPSG:4326')
        
        # Validate required parameters
        if not all([start_date, end_date, coordinates]):
            missing = []
            if not start_date: missing.append('start_date')
            if not end_date: missing.append('end_date') 
            if not coordinates: missing.append('coordinates')
            return jsonify({
                "error": f"Missing required parameters: {', '.join(missing)}"
            }), 400
        
        # Validate and convert parameters
        try:
            amc = int(amc) if amc else 2  # Default AMC = 2
            precipitation = float(precipitation) if precipitation else 10.0  # Default precipitation = 10mm
        except (ValueError, TypeError):
            return jsonify({
                "error": "Invalid parameter types. amc must be integer, precipitation must be number"
            }), 400
        
        # Validate coordinates
        if not isinstance(coordinates, list) or len(coordinates) < 3:
            return jsonify({
                "error": "Coordinates must be a list of at least 3 coordinate pairs"
            }), 400
        
        # Validate each coordinate pair
        for i, coord in enumerate(coordinates):
            if not isinstance(coord, list) or len(coord) != 2:
                return jsonify({
                    "error": f"Coordinate {i} must be a list of exactly 2 numbers [longitude, latitude]"
                }), 400
            
            try:
                lon, lat = float(coord[0]), float(coord[1])
                # Basic validation for geographic coordinates in WGS84
                if crs.upper() == 'EPSG:4326':
                    if not (-180 <= lon <= 180):
                        return jsonify({
                            "error": f"Longitude {lon} at coordinate {i} is out of range [-180, 180]"
                        }), 400
                    if not (-90 <= lat <= 90):
                        return jsonify({
                            "error": f"Latitude {lat} at coordinate {i} is out of range [-90, 90]"
                        }), 400
            except (ValueError, TypeError):
                return jsonify({
                    "error": f"Coordinate {i} must contain numeric values"
                }), 400
        
        # Validate AMC values
        if amc not in [1, 2, 3]:
            return jsonify({
                "error": "AMC (Antecedent Moisture Condition) must be 1, 2, or 3"
            }), 400
        
        # Create output directory
        os.makedirs(output_master, exist_ok=True)
        
        # Log the request parameters
        app.logger.info(f"Running Hydrosens analysis:")
        app.logger.info(f"  Date range: {start_date} to {end_date}")
        app.logger.info(f"  AMC: {amc}, Precipitation: {precipitation}mm")
        app.logger.info(f"  Coordinates: {len(coordinates)} points, CRS: {crs}")
        app.logger.info(f"  Output directory: {output_master}")
        
        # Run the Hydrosens analysis
        results = run_hydrosens_with_coordinates(
            coordinates=coordinates,
            start_date=start_date,
            end_date=end_date,
            output_dir=output_master,
            amc=amc,
            precipitation=precipitation,
            crs=crs
        )
        
        # Prepare successful response
        response_data = {
            "message": "Hydrosens analysis completed successfully",
            "parameters": {
                "start_date": start_date,
                "end_date": end_date,
                "amc": amc,
                "precipitation": precipitation,
                "coordinates": coordinates,
                "crs": crs,
                "num_coordinates": len(coordinates)
            },
            "results": results
        }
        
        app.logger.info(f"Analysis completed. Results: {len(results) if results else 0} dates processed")
        return jsonify(response_data), 200
        
    except Exception as e:
        app.logger.error(f"Error in Hydrosens analysis: {str(e)}")
        return jsonify({
            "error": f"Analysis failed: {str(e)}"
        }), 500


@app.route('/hydrosens/validate', methods=['POST'])
def validate_coordinates():
    """
    Endpoint to validate coordinates without running the full analysis.
    Useful for frontend validation.
    """
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = {
                'coordinates': json.loads(request.form.get('coordinates', '[]')),
                'crs': request.form.get('crs', 'EPSG:4326')
            }
        
        coordinates = data.get('coordinates')
        crs = data.get('crs', 'EPSG:4326')
        
        if not coordinates:
            return jsonify({"error": "No coordinates provided"}), 400
        
        # Validate coordinates format
        if not isinstance(coordinates, list) or len(coordinates) < 3:
            return jsonify({
                "error": "Coordinates must be a list of at least 3 coordinate pairs",
                "valid": False
            }), 400
        
        validation_errors = []
        
        for i, coord in enumerate(coordinates):
            if not isinstance(coord, list) or len(coord) != 2:
                validation_errors.append(f"Coordinate {i}: must be [longitude, latitude]")
                continue
            
            try:
                lon, lat = float(coord[0]), float(coord[1])
                if crs.upper() == 'EPSG:4326':
                    if not (-180 <= lon <= 180):
                        validation_errors.append(f"Coordinate {i}: longitude {lon} out of range")
                    if not (-90 <= lat <= 90):
                        validation_errors.append(f"Coordinate {i}: latitude {lat} out of range")
            except (ValueError, TypeError):
                validation_errors.append(f"Coordinate {i}: must contain numeric values")
        
        if validation_errors:
            return jsonify({
                "error": "Coordinate validation failed",
                "validation_errors": validation_errors,
                "valid": False
            }), 400
        
        # Calculate basic polygon properties
        from shapely.geometry import Polygon
        try:
            polygon = Polygon(coordinates)
            area_deg2 = polygon.area  # Area in square degrees (approximate)
            centroid = polygon.centroid
            
            return jsonify({
                "message": "Coordinates are valid",
                "valid": True,
                "properties": {
                    "num_coordinates": len(coordinates),
                    "crs": crs,
                    "approximate_area_deg2": area_deg2,
                    "centroid": [centroid.x, centroid.y],
                    "bounds": list(polygon.bounds)  # [minx, miny, maxx, maxy]
                }
            }), 200
            
        except Exception as e:
            return jsonify({
                "error": f"Invalid polygon geometry: {str(e)}",
                "valid": False
            }), 400
        
    except Exception as e:
        return jsonify({
            "error": f"Validation failed: {str(e)}",
            "valid": False
        }), 500


@app.route('/hydrosens/csv-file', methods=['GET'])
def get_csv_file():
    """Endpoint to retrieve the CSV output file."""
    output_master = os.getenv('OUTPUT_MASTER', '/app/data/output')
    csv_file_path = os.path.join(output_master, 'output.csv')

    if not os.path.exists(csv_file_path):
        return jsonify({"error": "CSV output file not found."}), 404

    return send_file(csv_file_path, mimetype='text/csv', as_attachment=True, download_name='output.csv')


@app.route('/export-latest-tifs', methods=['GET'])
def export_tifs_content():
    """Export TIF files as base64 encoded content."""
    output_master = os.getenv('OUTPUT_MASTER', '/app/data/output')
    tif_by_date = {}

    if not os.path.exists(output_master):
        return jsonify({"error": "Output folder does not exist"}), 404

    try:
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
                            app.logger.error(f"Error reading {file_path}: {str(e)}")
                
                if date_tifs:
                    tif_by_date[date_folder] = date_tifs

        return jsonify({
            "message": "Exported .tif file contents as base64",
            "tif_files": tif_by_date,
            "total_dates": len(tif_by_date)
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error exporting TIF files: {str(e)}")
        return jsonify({"error": f"Failed to export TIF files: {str(e)}"}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "Hydrosens API",
        "version": "2.0.0",
        "features": ["coordinate-based AOI", "coordinate validation"]
    }), 200


@app.route('/api/info', methods=['GET'])
def api_info():
    """Provide API documentation and usage information."""
    return jsonify({
        "service": "Hydrosens API",
        "version": "2.0.0",
        "description": "Hydrological analysis using coordinate-based Areas of Interest",
        "endpoints": {
            "/hydrosens": {
                "method": "POST",
                "description": "Run Hydrosens analysis",
                "content_type": "application/json",
                "required_fields": ["start_date", "end_date", "coordinates"],
                "optional_fields": ["amc", "precipitation", "crs"],
                "example_payload": {
                    "start_date": "2023-06-01",
                    "end_date": "2023-06-30",
                    "amc": 2,
                    "precipitation": 10.5,
                    "coordinates": [
                        [-120.5, 36.2],
                        [-120.4, 36.2],
                        [-120.4, 36.3],
                        [-120.5, 36.3]
                    ],
                    "crs": "EPSG:4326"
                }
            },
            "/hydrosens/validate": {
                "method": "POST",
                "description": "Validate coordinates without running analysis",
                "content_type": "application/json",
                "required_fields": ["coordinates"],
                "optional_fields": ["crs"]
            },
            "/export-latest-tifs": {
                "method": "GET",
                "description": "Export generated TIF files as base64"
            },
            "/health": {
                "method": "GET",
                "description": "Health check endpoint"
            }
        },
        "coordinate_format": {
            "description": "Coordinates should be provided as [longitude, latitude] pairs",
            "example": [[-120.5, 36.2], [-120.4, 36.2], [-120.4, 36.3], [-120.5, 36.3]],
            "minimum_points": 3,
            "supported_crs": ["EPSG:4326", "EPSG:32610", "EPSG:32611", "etc."],
            "default_crs": "EPSG:4326"
        },
        "parameter_ranges": {
            "amc": "1, 2, or 3 (Antecedent Moisture Condition)",
            "precipitation": "Any positive number (millimeters)",
            "longitude": "-180 to 180 (for EPSG:4326)",
            "latitude": "-90 to 90 (for EPSG:4326)"
        }
    }), 200


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    app.run(host="0.0.0.0", port=5050, debug=True)