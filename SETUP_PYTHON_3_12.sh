#!/bin/bash
# Setup Python 3.12 for hackerdogs-tools project

set -e

echo "=========================================="
echo "Setting up Python 3.12 for hackerdogs-tools"
echo "=========================================="

# Check if pyenv is available
if command -v pyenv &> /dev/null; then
    echo "✅ pyenv found"
    
    # Check if Python 3.12 is installed
    if pyenv versions | grep -q "3.12"; then
        echo "✅ Python 3.12 already installed"
        PYTHON_312=$(pyenv versions | grep "3.12" | head -1 | awk '{print $1}' | tr -d '*')
    else
        echo "📦 Installing Python 3.12.7..."
        pyenv install 3.12.7
        PYTHON_312="3.12.7"
    fi
    
    # Set local version
    echo "🔧 Setting Python 3.12 as local version..."
    pyenv local $PYTHON_312
    
    PYTHON_CMD="python3"
    
elif [ -f "/opt/homebrew/bin/python3.12" ]; then
    echo "✅ Found Homebrew Python 3.12"
    PYTHON_CMD="/opt/homebrew/bin/python3.12"
    
elif command -v python3.12 &> /dev/null; then
    echo "✅ Found system Python 3.12"
    PYTHON_CMD="python3.12"
    
else
    echo "❌ Python 3.12 not found!"
    echo ""
    echo "Please install Python 3.12 using one of these methods:"
    echo ""
    echo "Option 1: Using pyenv (Recommended)"
    echo "  brew install pyenv"
    echo "  pyenv install 3.12.7"
    echo "  pyenv local 3.12.7"
    echo ""
    echo "Option 2: Using Homebrew"
    echo "  brew install python@3.12"
    echo ""
    exit 1
fi

# Verify Python version
PYTHON_VERSION=$($PYTHON_CMD --version)
echo "✅ Using: $PYTHON_VERSION"

# Remove old venv
if [ -d "venv" ]; then
    echo "🗑️  Removing old virtual environment..."
    rm -rf venv
fi

# Create new venv
echo "📦 Creating new virtual environment with Python 3.12..."
$PYTHON_CMD -m venv venv

# Activate venv
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install crewai
echo "📥 Installing crewai..."
pip install crewai

# Verify installation
echo ""
echo "🧪 Verifying installation..."
if python3 -c "from crewai import Agent; print('✅ CrewAI works!')" 2>/dev/null; then
    echo ""
    echo "=========================================="
    echo "✅ SUCCESS! CrewAI is installed and working!"
    echo "=========================================="
    echo ""
    echo "To activate the virtual environment:"
    echo "  source venv/bin/activate"
    echo ""
else
    echo ""
    echo "❌ Installation verification failed"
    echo "Please check the error messages above"
    exit 1
fi

