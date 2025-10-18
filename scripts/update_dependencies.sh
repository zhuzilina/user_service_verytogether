#!/bin/bash

# Dependency Management Script for UserService
# This script helps update and compile dependencies using pip-tools

set -e  # Exit on any error

echo "🔄 Updating dependencies for UserService..."

# Check if pip-tools is installed
if ! command -v pip-compile &> /dev/null; then
    echo "📦 Installing pip-tools..."
    pip install pip-tools
fi

# Function to compile requirements
compile_requirements() {
    local file=$1
    echo "🔧 Compiling ${file}..."
    pip-compile "requirements/${file}.in" --upgrade
    echo "✅ Compiled ${file}.txt"
}

# Compile all requirement files
echo "📋 Compiling all requirement files..."
compile_requirements "base"
compile_requirements "local"
compile_requirements "production"

echo ""
echo "🎉 All dependencies updated successfully!"
echo ""
echo "📝 Generated files:"
echo "   - requirements/base.txt"
echo "   - requirements/local.txt"
echo "   - requirements/production.txt"
echo ""
echo "💡 To install dependencies:"
echo "   Development: pip install -r requirements/local.txt"
echo "   Production:  pip install -r requirements/production.txt"
echo ""
echo "🐳 To rebuild Docker image:"
echo "   docker-compose build --no-cache"