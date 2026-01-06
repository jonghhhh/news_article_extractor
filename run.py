#!/usr/bin/env python3
"""
News Article Extractor - Run Script
"""
import uvicorn
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Run the FastAPI application"""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    log_level = os.getenv("LOG_LEVEL", "info")
    reload = os.getenv("DEBUG", "false").lower() == "true"
    
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║            📰 News Article Extractor                     ║
    ╠══════════════════════════════════════════════════════════╣
    ║  Server: http://{host}:{port}                            
    ║  Docs:   http://{host}:{port}/docs                       
    ║  ReDoc:  http://{host}:{port}/redoc                      
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=reload,
    )


if __name__ == "__main__":
    main()
