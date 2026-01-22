#!/usr/bin/env python3
"""
Convert raw.json to aa.json
Remove panels with specified IDs: 3, 78, 79, 82, 83
"""
import json
import sys
from pathlib import Path


def replace_labels(obj):
    """
    Recursively replace labels in expr and legendFormat fields:
    - clickhouse_service -> control_plane_id in expr fields
    - {{instance}} -> {{pod}} in legendFormat fields

    Args:
        obj: The object to process (dict, list, or primitive)

    Returns:
        The modified object
    """
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == 'expr' and isinstance(value, str):
                # Replace clickhouse_service with control_plane_id
                obj[key] = value.replace(
                    'clickhouse_service=', 'control_plane_id=')
            elif key == 'legendFormat' and isinstance(value, str):
                # Replace {{instance}} with {{pod}}
                obj[key] = value.replace('{{instance}}', '{{pod}}')
            else:
                obj[key] = replace_labels(value)
    elif isinstance(obj, list):
        return [replace_labels(item) for item in obj]

    return obj


def convert_json(input_file, output_file, panels_to_remove=None):
    """
    Convert JSON file by:
    1. Removing specified panels
    2. Replacing clickhouse_service with control_plane_id in all expr fields

    Args:
        input_file: Input file path (raw.json)
        output_file: Output file path (aa.json)
        panels_to_remove: List of panel IDs to remove
    """
    if panels_to_remove is None:
        panels_to_remove = [3, 78, 79, 82, 83]

    # Read input file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File {input_file} does not exist")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Unable to parse JSON file - {e}")
        sys.exit(1)

    # Filter out panels with specified IDs
    if 'panels' in data:
        original_count = len(data['panels'])
        data['panels'] = [
            panel for panel in data['panels']
            if panel.get('id') not in panels_to_remove
        ]
        new_count = len(data['panels'])
        print(f"Original panel count: {original_count}")
        print(
            f"Removed {original_count - new_count} panels (IDs: {panels_to_remove})")
        print(f"Remaining panel count: {new_count}")

    # Replace labels in expressions and legendFormat fields
    print("Replacing labels:")
    print("  - 'clickhouse_service=' -> 'control_plane_id=' in expr fields")
    print("  - '{{instance}}' -> '{{pod}}' in legendFormat fields")
    data = replace_labels(data)

    # Transform templating variables
    print("Transforming templating variables...")
    if 'templating' in data and 'list' in data['templating']:
        for var in data['templating']['list']:
            var_name = var.get('name', '')

            # Transform service_name variable
            if var_name == 'service_name':
                var['definition'] = 'label_values(ClickHouse_Info,namespace)'
                var['regex'] = '/ns-(.+)/'
                if 'query' in var and isinstance(var['query'], dict) and 'query' in var['query']:
                    var['query']['query'] = 'label_values(ClickHouse_Info,namespace)'

            # Transform service_id variable
            elif var_name == 'service_id':
                var['definition'] = 'label_values(ClickHouse_Info{namespace=~"ns-$service_name"},control_plane_id)'
                if 'query' in var and isinstance(var['query'], dict) and 'query' in var['query']:
                    var['query']['query'] = 'label_values(ClickHouse_Info{namespace=~"ns-$service_name"},control_plane_id)'

    # Write output file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"\n✓ Conversion completed: {output_file}")
    except Exception as e:
        print(f"Error: Unable to write file - {e}")
        sys.exit(1)


def main():
    """Main function"""
    # Require input and output file paths as command line arguments
    if len(sys.argv) < 3:
        print("Usage: python3 convert.py <input_file> <output_file>")
        print("Example: python3 convert.py mix-in/raw.json mix-in/output.json")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])

    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print("-" * 50)

    convert_json(input_file, output_file)


if __name__ == "__main__":
    main()
