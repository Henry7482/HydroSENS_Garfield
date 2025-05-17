from flask import Flask, request, jsonify
from main_sentinel_update import run_hydrosens

app = Flask(__name__)

@app.route('/hydrosens', methods=['POST'])
def run_hydrosens_endpoint():
    output_master = request.form.get('output_master')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    amc = request.form.get('amc')
    p = request.form.get('p')

    if not output_master or not start_date or not end_date:
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        amc = int(amc) if amc else None
        p = int(p) if p else None

        data = run_hydrosens("./data", '2024-12-23', '2024-12-24', "./data", 2, 100)
        result = {"message": "Hydrosens run completed successfully", "data": data}
        print("Data:", data)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)