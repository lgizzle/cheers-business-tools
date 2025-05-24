import os
from logging_utils import setup_logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from werkzeug.utils import secure_filename
from report_processor import APReportProcessor
from deal_split_processor import DealSplitCalculator
from single_deal_calculator import SingleDealCalculator
from sales_tax_calculator import SalesTaxCalculator
from multi_product_calculator import MultiProductBuyingCalculator
from margin_calculator import MarginCalculator
import json
import shutil
from pathlib import Path
import traceback

app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['REPORT_FOLDER'] = 'reports'
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['REPORT_FOLDER'], exist_ok=True)
os.makedirs('logs', exist_ok=True)

# Initialize calculators
deal_calculator = DealSplitCalculator()
single_deal_calculator = SingleDealCalculator()
sales_tax_calculator = SalesTaxCalculator()
margin_calculator = MarginCalculator()

# Initialize the multi-product calculator instance
multi_product_calculator_instance = MultiProductBuyingCalculator()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    print("DEBUG: Landing page requested!")
    print("DEBUG: Will render index.html")
    return render_template('index.html')

@app.route('/debug-scenario')
def debug_scenario():
    """Debug page for scenario loading issues"""
    print("DEBUG: Scenario debug page requested")
    return render_template('debug_scenario.html')

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

@app.route('/api/delete-scenario/<n>', methods=['DELETE'])
def delete_scenario(n):
    """Delete a saved scenario by name."""
    try:
        print(f"Attempting to delete scenario: {n}")
        success = deal_calculator.delete_scenario(n)
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Scenario not found or could not be deleted"})
    except Exception as e:
        print(f"Error deleting scenario: {str(e)}")
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
    return render_template('multi_product_calculator.html')

@app.route('/api/export-multi-product-deal', methods=['POST'])
def export_multi_product_deal():
    """Export a distributor order sheet to Excel."""
    try:
        data = request.json

        # Get scenario name from request or use default
        scenario_name = data.get('name', 'Distributor Order')

        # Prepare data for the distributor export
        export_data = {
            'name': scenario_name,
            'products': data.get('products', []),
            'parameters': data.get('parameters', {})
        }

        # Generate distributor order Excel
        file_path = multi_product_calculator_instance.generate_distributor_order_excel(export_data)

        return send_file(file_path, as_attachment=True, download_name=os.path.basename(file_path))

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/calculate-multi-product-deal', methods=['POST'])
def calculate_multi_product_deal():
    """Calculate results for the Multi-Product Buying Calculator."""
    try:
        data = request.json

        # Calculate results using the shared instance
        results = multi_product_calculator_instance.calculate(data)

        # Return the results
        return jsonify({
            "success": True,
            "results": results
        })

    except Exception as e:
        print(f"Error calculating multi-product deal: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/optimize-multi-product-deal', methods=['POST'])
def optimize_multi_product_deal():
    """Run optimization for the Multi-Product Buying Calculator."""
    try:
        data = request.json

        # Run optimization using the shared instance
        results = multi_product_calculator_instance.optimize(data)

        # Return the results
        return jsonify({
            "success": True,
            "results": results
        })

    except Exception as e:
        print(f"Error optimizing multi-product deal: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/generate-multi-product-report', methods=['POST'])
def generate_multi_product_report():
    """Generate an Excel report for the Multi-Product Buying Calculator."""
    try:
        data = request.json

        # Generate the report using the shared instance
        file_path = multi_product_calculator_instance.generate_excel_report(data)

        # Return the file path for download
        filename = os.path.basename(file_path)
        return jsonify({
            "success": True,
            "filename": filename,
            "download_url": url_for('download_file', filename=filename)
        })

    except Exception as e:
        print(f"Error generating multi-product report: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/save-multi-product-scenario', methods=['POST'])
def save_multi_product_scenario():
    """Save a scenario for the Multi-Product Buying Calculator."""
    try:
        data = request.json

        # Save the scenario using the shared instance
        result = multi_product_calculator_instance.save_scenario(data)

        # Return success
        return jsonify({
            "success": True
        })

    except Exception as e:
        print(f"Error saving multi-product scenario: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/list-multi-product-scenarios')
def list_multi_product_scenarios():
    """List all scenarios for the Multi-Product Buying Calculator."""
    try:
        # List scenarios using the shared instance
        scenarios = multi_product_calculator_instance.list_scenarios()

        # Return the list
        return jsonify({
            "success": True,
            "scenarios": scenarios
        })

    except Exception as e:
        print(f"Error listing multi-product scenarios: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/delete-multi-product-scenario/<scenario_name>', methods=['DELETE'])
def delete_multi_product_scenario(scenario_name):
    """Delete a scenario for the Multi-Product Buying Calculator."""
    try:
        # Delete the scenario using the shared instance
        result = multi_product_calculator_instance.delete_scenario(scenario_name)

        # Return success
        return jsonify({
            "success": True
        })

    except Exception as e:
        print(f"Error deleting multi-product scenario: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/get-multi-product-scenario/<scenario_name>')
def get_multi_product_scenario(scenario_name):
    """Get a scenario for the Multi-Product Buying Calculator."""
    try:
        # Load the scenario using the shared instance
        scenario = multi_product_calculator_instance.load_scenario(scenario_name)

        # Return the scenario
        return jsonify({
            "success": True,
            "scenario": scenario
        })

    except Exception as e:
        print(f"Error getting multi-product scenario: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        })

# Route to delete a saved multi-product scenario
@app.route('/api/delete-multi-product-scenario/<scenario_name>', methods=['DELETE'])
def delete_multi_product_scenario(scenario_name):
    calculator = MultiProductBuyingCalculator()
    success = calculator.delete_scenario(scenario_name)
    return jsonify({"success": success})

# Margin/Markup Calculator routes
@app.route('/margin-calculator')
def margin_calculator_page():
    """Render the margin calculator page."""
    return render_template('margin_calculator.html')

@app.route('/api/generate-margin-report', methods=['POST'])
def generate_margin_report():
    """Generate a margin analysis report."""
    try:
        data = request.json

        # Validate required parameters
        if 'cost' not in data or not data['cost']:
            return jsonify({"success": False, "error": "Product cost is required"})

        # Set margin range if provided
        if 'min_margin' in data and 'max_margin' in data:
            margin_calculator.set_margin_range(data['min_margin'], data['max_margin'])

        # Calculate price at target margin
        price_at_target_margin = margin_calculator.calculate_price_from_margin(
            data['cost'], data['target_margin']
        )

        # Generate sensitivity data if needed
        sensitivity_data = margin_calculator.perform_sensitivity_analysis(
            data['cost'], data.get('current_price')
        )

        # Calculate current margin if current price is provided
        current_margin = None
        current_markup = None
        if 'current_price' in data and data['current_price']:
            current_margin = margin_calculator.calculate_margin_from_price(
                data['cost'], data['current_price']
            )
            current_markup = margin_calculator.calculate_markup_from_price(
                data['cost'], data['current_price']
            )

        # Prepare report data
        report_data = {
            'product_name': data.get('product_name', 'Unnamed Product'),
            'cost': data['cost'],
            'target_margin': data['target_margin'],
            'price_at_target_margin': price_at_target_margin,
            'current_price': data.get('current_price'),
            'current_margin': current_margin,
            'current_markup': current_markup,
            'sensitivity_data': sensitivity_data
        }

        # Generate a filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"margin_analysis_{timestamp}.xlsx"
        file_path = os.path.join(app.config['REPORT_FOLDER'], filename)

        # Generate the report
        margin_calculator.generate_report(report_data, file_path)

        return jsonify({
            "success": True,
            "filename": filename,
            "download_url": url_for('download_file', filename=filename)
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    # Set up logging
    setup_logging()
    # Run the Flask app with explicit host and port
    app.run(debug=True, host='0.0.0.0', port=8080)
