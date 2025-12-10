#!/usr/bin/env python3
"""
Quick start script for the Personal Finance Intelligence API.
Run this to start the development server.
"""
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting Personal Finance Intelligence API...")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("\n")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
