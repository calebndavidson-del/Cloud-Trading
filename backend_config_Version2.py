"""
Configuration, secrets, and cloud environment variables.
"""
import os

YAHOO_API_KEY = os.getenv("YAHOO_API_KEY", "")
# Add more configuration as needed