import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from werkzeug.utils import secure_filename
from report_processor import APReportProcessor
from deal_split_processor import DealSplitCalculator
from single_deal_calculator import SingleDealCalculator
from sales_tax_calculator import SalesTaxCalculator
from multi_product_calculator import MultiProductBuyingCalculator
import json
import shutil
from pathlib import Path
import traceback
import logging

app = Flask(__name__, static_url_path='/static')
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
sales_tax_calculator = SalesTaxCalculator()

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
            {
                "variety": item.get('variety', ''),
                "annual_sales": int(item.get('annual_sales', 0)),
                "inventory_on_hand": int(item.get('inventory_on_hand', 0))
            }
            for item in varieties_data
            if item.get('variety') and item.get('annual_sales')
        ]

        # Calculate the split
        results_df = deal_calculator.calculate_split(filtered_data, desired_total)

        # Convert to list of dictionaries for JSON response
        results = results_df.to_dict('records')

        # Convert NumPy types to standard Python types
        total_annual_sales = int(results_df['annual_sales'].sum())
        total_inventory_on_hand = int(results_df['inventory_on_hand'].sum())
        total_rounded_split = int(results_df['rounded_split'].sum())

        return jsonify({
            "success": True,
            "results": results,
            "total_annual_sales": total_annual_sales,
            "total_inventory_on_hand": total_inventory_on_hand,
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
            {
                "variety": item.get('variety', ''),
                "annual_sales": int(item.get('annual_sales', 0)),
                "inventory_on_hand": int(item.get('inventory_on_hand', 0))
            }
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
            {
                "variety": item.get('variety', ''),
                "annual_sales": int(item.get('annual_sales', 0)),
                "inventory_on_hand": int(item.get('inventory_on_hand', 0))
            }
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

# Sales Tax Calculator routes
@app.route('/sales-tax-calculator')
def sales_tax_calculator_page():
    return render_template('sales_tax_calculator.html')

@app.route('/api/calculate-sales-tax', methods=['POST'])
def calculate_sales_tax():
    try:
        data = request.json
        tax_data = data.get('tax_data', [])

        if not tax_data:
            return jsonify({"success": False, "error": "No tax data provided"})

        # Calculate results
        results = sales_tax_calculator.calculate_sales_from_tax(tax_data)

        # Convert DataFrame results to lists for JSON response
        sales_calculations = results['sales_calculations'].to_dict('records')
        tax_calculations = results['tax_calculations'].to_dict('records')

        # Handle NumPy types for JSON serialization
        def convert_numpy_types(item):
            for key, value in item.items():
                if 'numpy' in str(type(value)):
                    item[key] = float(value)
            return item

        sales_calculations = [convert_numpy_types(item) for item in sales_calculations]
        tax_calculations = [convert_numpy_types(item) for item in tax_calculations]

        return jsonify({
            "success": True,
            "results": {
                "sales_calculations": sales_calculations,
                "tax_calculations": tax_calculations
            }
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/generate-sales-tax-report', methods=['POST'])
def generate_sales_tax_report():
    try:
        data = request.json
        tax_data = data.get('tax_data', [])

        if not tax_data:
            return jsonify({"success": False, "error": "No tax data provided"})

        # Generate a filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sales_tax_{timestamp}.xlsx"
        file_path = os.path.join(app.config['REPORT_FOLDER'], filename)

        # Generate the report
        sales_tax_calculator.generate_report(tax_data, file_path)

        return jsonify({
            "success": True,
            "filename": filename,
            "download_url": url_for('download_file', filename=filename)
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})

@app.route('/view-sample-report')
def view_sample_report():
    """Generate a report using sample data for demonstration purposes."""
    try:
        # Path to the real source file in the project root
        sample_file_path = os.path.join('.', 'Victory Spirits LLC dba Cheers Liquor Mart_A_P Aging Detail Report-2.xlsx')

        # Check if source file exists, if not, show an error
        if not os.path.exists(sample_file_path):
            flash('Sample data file not found. Please contact the administrator.')
            return redirect(url_for('index'))

        # Create a temporary copy of the source file to process
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f'sample_temp_{timestamp}.xlsx')
        shutil.copy2(sample_file_path, temp_file_path)

        # Process the report
        processor = APReportProcessor(temp_file_path)
        output_file = processor.generate_report()

        # Pass the generated file path to the template
        return render_template('success.html',
                              filename=os.path.basename(output_file),
                              is_sample=True)
    except Exception as e:
        flash(f'Error processing sample file: {str(e)}')
        return redirect(url_for('index'))

# Multi-Product Buying Calculator routes
@app.route('/multi-product-calculator')
def multi_product_calculator():
    """Render the multi-product buying calculator page."""
    return render_template('multi_product_calculator.html')

@app.route('/api/calculate-multi-product-deal', methods=['POST'])
def calculate_multi_product_deal():
    """Calculate multi-product deal metrics."""
    data = request.get_json()

    # Initialize calculator
    calculator = MultiProductBuyingCalculator()

    # Set parameters
    calculator.set_parameters(
        data['parameters']['small_deal_minimum'],
        data['parameters']['bulk_deal_minimum'],
        data['parameters']['payment_terms']
    )

    # Add products
    for product in data['products']:
        calculator.add_product(
            product['product_name'],
            product['current_price'],
            product['bulk_price'],
            product['cases_on_hand'],
            product['cases_per_year'],
            product['bottles_per_case'],
            product['bulk_quantity']
        )

    # Calculate results
    results = calculator.calculate()

    return jsonify(results)

@app.route('/api/generate-multi-product-deal-report', methods=['POST'])
def generate_multi_product_deal_report():
    """Generate Excel report for multi-product deal."""
    data = request.get_json()

    # Initialize calculator
    calculator = MultiProductBuyingCalculator()

    # Set parameters
    calculator.set_parameters(
        data['parameters']['small_deal_minimum'],
        data['parameters']['bulk_deal_minimum'],
        data['parameters']['payment_terms']
    )

    # Generate report
    try:
        filename = calculator.generate_report(data['results'])
        return jsonify({"filename": filename})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/save-multi-product-scenario', methods=['POST'])
def save_multi_product_scenario():
    """Save a multi-product scenario."""
    data = request.get_json()

    # Initialize calculator
    calculator = MultiProductBuyingCalculator()

    # Set parameters
    calculator.set_parameters(
        data['parameters']['small_deal_minimum'],
        data['parameters']['bulk_deal_minimum'],
        data['parameters']['payment_terms']
    )

    # Add products
    for product in data['products']:
        calculator.add_product(
            product['product_name'],
            product['current_price'],
            product['bulk_price'],
            product['cases_on_hand'],
            product['cases_per_year'],
            product['bottles_per_case'],
            product['bulk_quantity']
        )

    # Save scenario
    try:
        filename = calculator.save_scenario(data['name'])
        return jsonify({"success": True, "filename": filename})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/list-multi-product-scenarios')
def list_multi_product_scenarios():
    """List all saved multi-product scenarios."""
    calculator = MultiProductBuyingCalculator()
    scenarios = calculator.list_scenarios()
    return jsonify({"scenarios": scenarios})

@app.route('/api/get-multi-product-scenario/<scenario_name>')
def get_multi_product_scenario(scenario_name):
    """Get a specific multi-product scenario."""
    logging.basicConfig(filename='logs/app.log', level=logging.DEBUG)
    logging.info(f"Attempting to load scenario: {scenario_name}")

    calculator = MultiProductBuyingCalculator()

    try:
        # Log available scenarios
        available_scenarios = calculator.list_scenarios()
        logging.info(f"Available scenarios: {available_scenarios}")

        # Check if scenario name matches any available scenario (case-insensitive)
        scenario_name_lower = scenario_name.lower()
        matching_scenarios = [s for s in available_scenarios if s.lower() == scenario_name_lower]
        if matching_scenarios:
            logging.info(f"Found matching scenario: {matching_scenarios[0]}")
            scenario_name = matching_scenarios[0]  # Use the exact case from available scenarios

        # Try to load the scenario
        success = calculator.load_scenario(scenario_name)

        if not success:
            # Check if file exists
            import os
            filename = f"scenarios/{scenario_name.lower().replace(' ', '_')}.json"
            logging.error(f"Failed to load scenario. File exists: {os.path.exists(filename)}")
            return jsonify({"error": f"Scenario not found: {scenario_name}"})

        logging.info(f"Successfully loaded scenario: {scenario_name}")

        return jsonify({
            "parameters": {
                "small_deal_minimum": calculator.small_deal_minimum,
                "bulk_deal_minimum": calculator.bulk_deal_minimum,
                "payment_terms": calculator.payment_terms
            },
            "products": calculator.products
        })
    except Exception as e:
        logging.error(f"Error loading scenario: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({"error": f"Error loading scenario: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
