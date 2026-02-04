#!/bin/bash

# CornHub Startup Script
echo "🌽 Starting CornHub Repository Manager..."

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    echo "❌ Error: Please run this script from the project root directory (where app/ folder is located)"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "dbms" ]; then
    echo "❌ Error: Virtual environment 'dbms' not found. Please create it first:"
    echo "   python3 -m venv dbms"
    echo "   source dbms/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source dbms/bin/activate

# Check if required packages are installed
echo "🔍 Checking dependencies..."
python -c "import fastapi, sqlalchemy, pymongo, git" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Error: Required packages not installed. Installing now..."
    pip install -r requirements.txt
fi

# Check database connections
echo "🗄️  Checking database connections..."

# Check PostgreSQL connection
python -c "
from app.database_sessions import engine
from sqlalchemy.sql import text
try:
    with engine.connect() as connection:
        connection.execute(text('SELECT 1'))
    print('✅ PostgreSQL connection: OK')
except Exception as e:
    print('❌ PostgreSQL connection failed:', e)
    print('   Please ensure PostgreSQL is running and database exists')
    print('   Connection string: postgresql://devuser:****@localhost:5432/devdb')
" 2>/dev/null

# Check MongoDB connection
python -c "
import pymongo
try:
    client = pymongo.MongoClient('mongodb://localhost:27017')
    client.server_info()
    print('✅ MongoDB connection: OK')
except Exception as e:
    print('❌ MongoDB connection failed:', e)
    print('   Please ensure MongoDB is running')
" 2>/dev/null

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p tmp/repos

echo ""
echo "🚀 Starting CornHub server..."
echo "   API Documentation: http://localhost:8080/docs"
echo "   Frontend Interface: http://localhost:8080/"
echo "   Press Ctrl+C to stop"
echo ""

# Start the server
uvicorn app.main:app --reload --log-level=debug --port 8080 --host 0.0.0.0