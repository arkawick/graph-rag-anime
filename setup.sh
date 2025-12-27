#!/bin/bash

# Setup script for Neo4j Graph RAG

echo "=== Neo4j Graph RAG Setup ==="
echo

# Check Python version
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
echo "Creating virtual environment..."
python -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Download spaCy model
echo "Downloading spaCy model..."
python -m spacy download en_core_web_sm

# Create .env file
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ Created .env file - please edit and add your API keys"
else
    echo "✓ .env file already exists"
fi

# Start Neo4j
echo
echo "Starting Neo4j..."
docker-compose up -d

# Wait for Neo4j to be ready
echo "Waiting for Neo4j to be ready..."
sleep 10

echo
echo "=== Setup Complete! ==="
echo
echo "Next steps:"
echo "1. Edit .env and add your API keys (if using OpenAI)"
echo "2. Put documents in data/documents/"
echo "3. Run: python cli.py ingest --source data/documents"
echo "4. Run: python cli.py query 'Your question here'"
echo "5. Or launch web UI: python cli.py serve"
echo
echo "Neo4j Browser: http://localhost:7474 (neo4j/password123)"
echo
