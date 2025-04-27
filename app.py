from flask import Flask, request, jsonify
from main_sentinel_update import run_hydrosens

app = Flask(__name__)

@app.route('/run_hydrosens', methods=['POST'])
def run_hydrosens_endpoint():
    data = request.get_json()
    output_master = data.get('output_master')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    amc = data.get('amc')
    p = data.get('p')
    
    if not output_master or not start_date or not end_date:
        return jsonify({"error": "Missing required parameters"}), 400
    
    try:
        amc = int(amc) if amc is not None else None
        p = int(p) if p is not None else None
        
        run_hydrosens(output_master, start_date, end_date, output_master, amc, p)
        result = {"message": "Hydrosens run completed successfully"}
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)