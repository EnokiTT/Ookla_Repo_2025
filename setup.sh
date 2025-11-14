#!/bin/bash

# Installation script for macOS/Linux
# This script sets up the Python environment and installs all dependencies

echo "================================"
echo "Ookla Data Analysis Setup Script"
echo "================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Check if we're in the correct directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found. Please run this script from the project root directory."
    exit 1
fi

# Ask user if they want to create a virtual environment
read -p "Do you want to create a virtual environment? (recommended) [Y/n]: " create_venv
create_venv=${create_venv:-Y}

if [[ $create_venv =~ ^[Yy]$ ]]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    
    if [ $? -eq 0 ]; then
        echo "✅ Virtual environment created successfully"
        echo ""
        echo "🔄 Activating virtual environment..."
        source venv/bin/activate
        echo "✅ Virtual environment activated"
    else
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
else
    echo ""
    echo "⚠️  Installing packages globally (not recommended)"
fi

echo ""
echo "📥 Upgrading pip..."
pip install --upgrade pip

echo ""
echo "📥 Installing required packages..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All packages installed successfully!"
    echo ""
    echo "================================"
    echo "Setup Complete!"
    echo "================================"
    echo ""
    
    if [[ $create_venv =~ ^[Yy]$ ]]; then
        echo "To activate the virtual environment in the future, run:"
        echo "  source venv/bin/activate"
        echo ""
        echo "To deactivate the virtual environment, run:"
        echo "  deactivate"
        echo ""
    fi
    
    echo "To start Jupyter Notebook, run:"
    echo "  jupyter notebook notebook/Ookla_Extractor.ipynb"
    echo ""
else
    echo ""
    echo "❌ Installation failed. Please check the error messages above."
    exit 1
fi
