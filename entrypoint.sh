#!/bin/bash

set -e

echo "=========================================="
echo "Mavvrik SDK Assistant - Starting"
echo "=========================================="
echo ""

# Function to check if a required environment variable is set
check_env_var() {
    local var_name=$1
    local var_value=$(eval echo \$$var_name)

    if [ -z "$var_value" ]; then
        echo "❌ ERROR: $var_name is not set"
        return 1
    else
        echo "✅ $var_name is set"
        return 0
    fi
}

echo "🔍 Checking environment variables..."
echo ""

# Check required API keys
all_good=true

check_env_var "OPENAI_API_KEY" || all_good=false
check_env_var "TAVILY_API_KEY" || all_good=false
check_env_var "MVK_API_KEY" || all_good=false

echo ""

if [ "$all_good" = false ]; then
    echo "❌ Missing required environment variables"
    echo "Please set all required variables in your .env file"
    echo ""
    echo "Required variables:"
    echo "  - OPENAI_API_KEY"
    echo "  - TAVILY_API_KEY"
    echo "  - MVK_API_KEY"
    echo ""
    exit 1
fi

# Check if PDF exists
if [ ! -f "./docs/mvk_sdk_documentation.pdf" ]; then
    echo "⚠️  WARNING: PDF documentation not found at ./docs/mvk_sdk_documentation.pdf"
    echo "The application will start but SDK queries will not work."
    echo ""
fi

# Run initialization script
echo "🚀 Running initialization..."
python src/init.py

if [ $? -ne 0 ]; then
    echo "❌ Initialization failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Starting Chainlit Application"
echo "=========================================="
echo ""
echo "Access the application at: http://localhost:${CHAINLIT_PORT:-8000}"
echo ""

# Start Chainlit
cd src
exec chainlit run app.py --host 0.0.0.0 --port ${CHAINLIT_PORT:-8000}
