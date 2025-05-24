import os
import json

SCENARIO_DIR = 'scenarios'
PARAM_KEYS = ['small_deal_minimum', 'bulk_deal_minimum', 'payment_terms', 'daily_interest_rate']

def migrate_scenario_file(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)

    # Only migrate if 'parameters' key is missing
    if 'parameters' not in data:
        params = {}
        for key in PARAM_KEYS:
            if key in data:
                params[key] = data.pop(key)
        # If any parameters found, migrate
        if params:
            new_data = {
                'parameters': params,
                'products': data.get('products', [])
            }
            # Backup original file
            backup_path = filepath + '.bak'
            os.rename(filepath, backup_path)
            # Write migrated file
            with open(filepath, 'w') as f:
                json.dump(new_data, f, indent=2)
            print(f"Migrated: {filepath} (backup saved as {backup_path})")
        else:
            print(f"No migration needed: {filepath}")
    else:
        print(f"Already migrated: {filepath}")

def migrate_all_scenarios():
    for filename in os.listdir(SCENARIO_DIR):
        if filename.endswith('.json'):
            migrate_scenario_file(os.path.join(SCENARIO_DIR, filename))

if __name__ == '__main__':
    migrate_all_scenarios()
