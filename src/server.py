#!/usr/bin/env python3
"""
Neural Memory Server
Main Flask application entry point
"""

from flask import Flask
from flask_cors import CORS
import os
import sqlite3

from mcp_sse_handler import create_mcp_endpoint


def init_database(db_path):
    """Initialize SQLite database"""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            timestamp TEXT,
            embedding_vector BLOB
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized: {db_path}")


def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    CORS(app)
    
    # Configuration
    db_path = os.getenv('DB_PATH', '/app/data/memory.db')
    
    # Initialize database
    init_database(db_path)
    
    # Register MCP endpoint
    create_mcp_endpoint(app)
    
    return app


def main():
    """Run the server"""
    print("=" * 50)
    print("🧠 Neural Memory MCP Server")
    print("=" * 50)
    
    # Run embedding consistency check
    try:
        from embedding_check import run_check
        run_check()
    except Exception as e:
        print(f"⚠️  Consistency check skipped: {e}")
    
    # Create and run app
    app = create_app()
    
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    print(f"\n🚀 Server starting on port {port}")
    print(f"   Debug mode: {debug}")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=debug)


if __name__ == '__main__':
    main()
