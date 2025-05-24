import os
import json

def scenario_filename(scenarios_dir, scenario_name):
    return os.path.join(scenarios_dir, f"{scenario_name.lower().replace(' ', '_')}.json")

def save_scenario_file(scenarios_dir, scenario_name, products, small_deal_minimum, bulk_deal_minimum, payment_terms):
    os.makedirs(scenarios_dir, exist_ok=True)
    filename = scenario_filename(scenarios_dir, scenario_name)
    data = {
        'products': products,
        'small_deal_minimum': small_deal_minimum,
        'bulk_deal_minimum': bulk_deal_minimum,
        'payment_terms': payment_terms
    }
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    return filename

def load_scenario_file(scenarios_dir, scenario_name):
    filename = scenario_filename(scenarios_dir, scenario_name)
    if not os.path.exists(filename):
        return None
    with open(filename, 'r') as f:
        return json.load(f)

def delete_scenario_file(scenarios_dir, scenario_name):
    filename = scenario_filename(scenarios_dir, scenario_name)
    if os.path.exists(filename):
        os.remove(filename)
        return True
    return False

def list_scenario_files(scenarios_dir):
    scenarios = []
    for filename in os.listdir(scenarios_dir):
        if filename.endswith('.json'):
            scenario_name = filename[:-5].replace('_', ' ').title()
            scenarios.append(scenario_name)
    return scenarios

# Single-file scenario management for DealSplitCalculator

def load_all_scenarios(scenarios_file):
    if not os.path.exists(scenarios_file):
        return {}
    with open(scenarios_file, 'r') as f:
        return json.load(f)

def save_all_scenarios(scenarios_file, scenarios_dict):
    with open(scenarios_file, 'w') as f:
        json.dump(scenarios_dict, f, indent=4)
