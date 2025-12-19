"""
Vercel serverless function wrapper for FastAPI.
This allows the FastAPI app to run on Vercel's serverless platform.
"""

from main import app

# Export the app for Vercel
handler = app

