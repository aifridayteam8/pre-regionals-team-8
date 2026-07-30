#!/usr/bin/env python
"""
Main entry point for the AI-Powered Incident Report Generator Backend.
This script runs the Flask application from the backend directory.
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
