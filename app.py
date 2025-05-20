import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from werkzeug.utils import secure_filename
from report_processor import APReportProcessor
from deal_split_processor import DealSplitCalculator
from single_deal_calculator import SingleDealCalculator
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['REPORT_FOLDER'] = 'reports'
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['REPORT_FOLDER'], exist_ok=True)

# Initialize calculators
deal_calculator = DealSplitCalculator()
single_deal_calculator = SingleDealCalculator()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    print("DEBUG: Landing page requested!")
    print("DEBUG: Will render index.html")
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        try:
            # Process the AP report
            processor = APReportProcessor(file_path)
            output_file = processor.generate_report()

            # Pass the generated file path to the template
            return render_template('success.html', filename=os.path.basename(output_file))
        except Exception as e:
            flash(f'Error processing file: {str(e)}')
            return redirect(url_for('index'))
    else:
        flash('Invalid file type. Please upload an Excel file (.xlsx, .xls)')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['REPORT_FOLDER'], filename), as_attachment=True)

# Deal Split Calculator routes
@app.route('/deal-calculator')
def deal_calculator_page():
    scenarios = deal_calculator.get_all_scenarios()
    return render_template('deal_calculator.html', scenarios=scenarios)

@app.route('/api/calculate-deal', methods=['POST'])
def calculate_deal():
    try:
        data = request.json
        varieties_data = data.get('varieties', [])
        desired_total = int(data.get('desired_total', 0))

        # Filter out empty rows
        filtered_data = [
            {"variety": item.get('variety', ''), "annual_sales": int(item.get('annual_sales', 0))}
            for item in varieties_data
            if item.get('variety') and item.get('annual_sales')
        ]

        # Calculate the split
        results_df = deal_calculator.calculate_split(filtered_data, desired_total)

        # Convert to list of dictionaries for JSON response
        results = results_df.to_dict('records')

        # Convert NumPy types to standard Python types
        total_annual_sales = int(results_df['annual_sales'].sum())
        total_rounded_split = int(results_df['rounded_split'].sum())

        return jsonify({
            "success": True,
            "results": results,
            "total_annual_sales": total_annual_sales,
            "total_rounded_split": total_rounded_split
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/save-scenario', methods=['POST'])
def save_scenario():
    try:
        data = request.json
        scenario_name = data.get('name', '')
        varieties_data = data.get('varieties', [])

        # Filter out empty rows
        filtered_data = [
            {"variety": item.get('variety', ''), "annual_sales": int(item.get('annual_sales', 0))}
            for item in varieties_data
            if item.get('variety') and item.get('annual_sales')
        ]

        # Save the scenario
        deal_calculator.save_scenario(scenario_name, filtered_data)

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/get-scenario/<n>')
def get_scenario(n):
    try:
        scenario = deal_calculator.get_scenario(n)
        if scenario:
            return jsonify({"success": True, "scenario": scenario})
        else:
            return jsonify({"success": False, "error": "Scenario not found"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/get-all-scenarios')
def get_all_scenarios():
    try:
        scenarios = deal_calculator.get_all_scenarios()
        return jsonify({"success": True, "scenarios": scenarios})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/generate-deal-report', methods=['POST'])
def generate_deal_report():
    try:
        data = request.json
        varieties_data = data.get('varieties', [])
        desired_total = int(data.get('desired_total', 0))

        # Filter out empty rows
        filtered_data = [
            {"variety": item.get('variety', ''), "annual_sales": int(item.get('annual_sales', 0))}
            for item in varieties_data
            if item.get('variety') and item.get('annual_sales')
        ]

        # Generate a filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"deal_split_{timestamp}.xlsx"
        file_path = os.path.join(app.config['REPORT_FOLDER'], filename)

        # Generate the report
        deal_calculator.generate_report(filtered_data, desired_total, file_path)

        return jsonify({
            "success": True,
            "filename": filename,
            "download_url": url_for('download_file', filename=filename)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# Single Deal Calculator routes
@app.route('/single-deal-calculator')
def single_deal_calculator_page():
    return render_template('single_deal_calculator.html')

@app.route('/api/calculate-single-deal', methods=['POST'])
def calculate_single_deal():
    try:
        data = request.json

        # Validate required parameters
        required_params = [
            'smaller_deal_qty',
            'bulk_deal_qty',
            'price_per_bottle_smaller',
            'price_per_bottle_bulk',
            'annual_sales_volume',
            'vendor_terms',
            'bottles_per_case'
        ]

        for param in required_params:
            if param not in data or not data[param]:
                return jsonify({"success": False, "error": f"Missing required parameter: {param}"})

        # Calculate results
        results = single_deal_calculator.calculate_deal(data)

        return jsonify({
            "success": True,
            "results": results
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/generate-single-deal-report', methods=['POST'])
def generate_single_deal_report():
    try:
        data = request.json

        # Validate required parameters
        required_params = [
            'smaller_deal_qty',
            'bulk_deal_qty',
            'price_per_bottle_smaller',
            'price_per_bottle_bulk',
            'annual_sales_volume',
            'vendor_terms',
            'bottles_per_case'
        ]

        for param in required_params:
            if param not in data or not data[param]:
                return jsonify({"success": False, "error": f"Missing required parameter: {param}"})

        # Generate a filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"single_deal_{timestamp}.xlsx"
        file_path = os.path.join(app.config['REPORT_FOLDER'], filename)

        # Generate the report
        single_deal_calculator.generate_report(data, file_path)

        return jsonify({
            "success": True,
            "filename": filename,
            "download_url": url_for('download_file', filename=filename)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
