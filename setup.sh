#!/bin/bash
# setup.sh - Script to set up the family tree project

# Create virtual environment
echo "Creating virtual environment..."
python -m venv venv

# Activate virtual environment
case "$(uname -s)" in
    CYGWIN*|MINGW*|MSYS*)
        # Windows
        source venv/Scripts/activate
        ;;
    *)
        # Linux/Mac
        source venv/bin/activate
        ;;
esac

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Make scripts executable
chmod +x family_tree_workflow.py

# Check if installation was successful
if [ $? -eq 0 ]; then
    echo "Setup completed successfully!"
    echo "To activate the environment, run: source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)"
    echo "To generate a family tree, run: python family_tree_workflow.py"
else
    echo "Error: Failed to install dependencies."
    echo "Please check the error messages above."
fi