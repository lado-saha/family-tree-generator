#!/usr/bin/env python
"""
Simplified Family Tree Generation Workflow
Focuses primarily on the interactive HTML visualization
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Import our modules (make sure the files are in the same directory)
# We're using exec() to avoid import errors if you run this directly
try:
    # First, try direct import
    from family_tree_generator import create_family_tree
    # from family_tree_visualizer import run_visualization
    from sql_import_exporter import process_family_data
except ImportError:
    # If that fails, check if the files exist and exec them
    module_files = {
        'family_tree_generator.py': 'create_family_tree',
        'family_tree_visualizer.py': 'run_visualization',
        'sql_import_exporter.py': 'process_family_data'
    }

    for module_file, main_func in module_files.items():
        if not os.path.exists(module_file):
            print(f"Error: Required module file {module_file} not found.")
            print("Please make sure all component files are in the same directory.")
            sys.exit(1)

        # Execute the file content to get access to its functions
        with open(module_file, 'r') as f:
            exec(f.read())


def create_output_directory(base_dir='family_tree_output'):
    """Create a timestamped output directory"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = f"{base_dir}_{timestamp}"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    return output_dir


def simplified_workflow(output_dir, num_families=15, num_generations=4):
    """Run a simplified workflow focusing only on the interactive visualization"""
    print("=" * 80)
    print(f"SIMPLIFIED FAMILY TREE WORKFLOW")
    print(f"Output directory: {output_dir}")
    print("=" * 80)

    # Step 1: Generate the family tree data
    print("\n[Step 1/3] Generating family tree data...")
    json_path = os.path.join(output_dir, 'family_tree.json')
    create_family_tree(output_file=json_path,
                       num_families=num_families, num_generations=num_generations)

    # Step 2: Import into SQLite
    print("\n[Step 2/3] Creating SQLite database...")
    db_path = os.path.join(output_dir, 'family_tree.db')
    process_family_data(json_path=json_path, db_path=db_path)

    # Step 3: Generate only the interactive visualization
    print("\n[Step 3/3] Creating interactive visualization...")
    viz_dir = os.path.join(output_dir, 'visualization')
    if not os.path.exists(viz_dir):
        os.makedirs(viz_dir)

    # Load the data
    with open(json_path, 'r') as f:
        data = json.load(f)
    people_data = data['people']

    # Create interactive visualization
    try:
        import pyvis
        from pyvis.network import Network
        import networkx as nx

        # Build the graph
        from family_tree_visualizer import build_family_graph
        G = build_family_graph(people_data)

        # Create visualization using the pyvis
        from family_tree_visualizer import visualize_with_pyvis
        index_path = os.path.join(
            output_dir, 'index.html')
        visualize_with_pyvis(G, output_file=index_path,
                             height="800px", width="100%")

        # Create an index.html file that redirects to the interactive visualization
        # index_path = os.path.join(output_dir, 'index.html')
        index_path = os.path.join(output_dir, 'index.html')
        print(f"To view it, open: {index_path}")
    except ImportError:
        print("Error: Pyvis or NetworkX is not installed. Cannot create interactive visualization.")
        print("Install with: pip install pyvis networkx")
        return None

    print("\n" + "=" * 80)
    print(f"WORKFLOW COMPLETE!")
    print(f"All outputs saved to: {output_dir}")
    print(f"Main visualization: {index_path}")
    print("=" * 80)

    return {
        'output_dir': output_dir,
        'json_path': json_path,
        'db_path': db_path,
        'interactive_viz': index_path,
        'index_path': index_path
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Generate a family tree with focus on interactive visualization')
    parser.add_argument('--families', type=int, default=4,
                        help='Number of initial families to create')
    parser.add_argument('--generations', type=int, default=4,
                        help='Number of generations to simulate')
    parser.add_argument('--output-dir', type=str,
                        help='Output directory (defaults to timestamped directory)')

    args = parser.parse_args()

    # Create output directory if not specified
    output_dir = args.output_dir if args.output_dir else create_output_directory()

    # Run the simplified workflow
    results = simplified_workflow(
        output_dir=output_dir,
        num_families=args.families,
        num_generations=args.generations
    )

    if results:
        print("\nTo view the interactive visualization:")
        print(
            f"1. Open this file in your browser: {results['index_path']} (automatically redirects)")
        print(f"2. Or directly open: {results['interactive_viz']}")
