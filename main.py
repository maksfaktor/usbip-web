"""
Main Entry Point for Orange USB/IP Web Interface
=================================================

This file serves as the application entry point for the Gunicorn WSGI server.
When running with Gunicorn, it imports the Flask app instance from app.py.
When running directly (python main.py), it starts the development server.

File: main.py
Project: Orange USB/IP Web Interface
Purpose: Application entry point and development server launcher
"""

# Import the Flask application instance from the main application module
# The 'noqa: F401' comment tells linters to ignore the "imported but unused" warning
# because Gunicorn needs this import to find the 'app' object
from app import app  # noqa: F401

# This block only executes when running the file directly (not via Gunicorn)
# Gunicorn imports 'app' from this module but doesn't execute __main__
if __name__ == "__main__":
    # Start Flask's built-in development server
    # Parameters:
    #   host="0.0.0.0" - Listen on all network interfaces (not just localhost)
    #                    This allows access from other devices on the network
    #   port=5000      - Standard Flask development port
    #   debug=True     - Enable debug mode with auto-reload and detailed errors
    #                    WARNING: Never use debug=True in production!
    app.run(host="0.0.0.0", port=5000, debug=True)
