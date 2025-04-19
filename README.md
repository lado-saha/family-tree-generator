# Family Tree Generator

A tool to generate, visualize, and explore complex family trees with realistic relationships.

## Setup

1. Clone this repository or download the files
2. Run the setup script to create a virtual environment and install dependencies:

   ```bash
   # Make the setup script executable if needed
   chmod +x setup.sh

   # Run the setup script
   ./setup.sh
   ```

3. Activate the virtual environment:

   ```bash
   # On Linux/Mac
   source venv/bin/activate

   # On Windows
   venv\Scripts\activate
   ```

## Usage

Generate a family tree with the default settings:

```bash
python family_tree_workflow.py
```

Customize the family tree:

```bash
python family_tree_workflow.py --families 8 --generations 5
```

## Options

- `--families`: Number of initial families to create (default: 4)
- `--generations`: Number of generations to simulate (default: 4)
- `--output-dir`: Custom output directory (default: timestamped directory)

## Viewing the Visualization

After running the workflow, open the generated `index.html` file in a web browser to explore the family tree interactively.

## Requirements

The setup script will install all required dependencies, which include:

- names
- faker
- networkx
- pyvis
