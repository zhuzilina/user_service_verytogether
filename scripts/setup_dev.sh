#!/bin/bash

# Development Setup Script for UserService
# This script sets up the development environment

set -e  # Exit on any error

echo "🚀 Setting up UserService development environment..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install pip-tools
echo "📦 Installing pip-tools..."
pip install pip-tools

# Install development dependencies
echo "📚 Installing development dependencies..."
pip install -r requirements/local.txt

# Create environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration"
fi

# Create logs directory
echo "📁 Creating logs directory..."
mkdir -p logs

# Run database migrations
echo "🗄️ Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# Create superuser (optional)
echo ""
read -p "Do you want to create a superuser? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python manage.py createsuperuser
fi

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "🎯 Next steps:"
echo "   1. Edit .env file with your configuration"
echo "   2. Run 'python manage.py runserver 8001' to start the server"
echo "   3. Visit http://localhost:8001/docs/ for API documentation"
echo ""
echo "🔧 Useful commands:"
echo "   - Start server: python manage.py runserver 8001"
echo "   - Run tests: pytest"
echo "   - Update dependencies: ./scripts/update_dependencies.sh"
echo "   - Format code: black . && isort ."
echo "   - Lint code: flake8"