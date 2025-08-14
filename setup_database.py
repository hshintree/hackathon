#!/usr/bin/env python3
"""
Database setup script for the trading agent.
This script creates all tables defined in the schema.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database.schema import (
	create_database_engine, 
	create_tables, 
	get_session_maker,
	Base
)
from sqlalchemy import text


def main():
	"""Set up the database with all required tables."""
	try:
		print("🔧 Setting up database...")
		
		# Create engine
		engine = create_database_engine()
		print("✅ Database engine created successfully")
		
		# Test connection
		with engine.connect() as conn:
			result = conn.execute(text("SELECT version()"))
			version = result.fetchone()[0]
			print(f"✅ Connected to PostgreSQL: {version}")
			
			# Check pgvector extension
			result = conn.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
			if result.fetchone():
				print("✅ pgvector extension is installed")
			else:
				print("❌ pgvector extension not found")
				return False
		
		# Create all tables
		print("📊 Creating database tables...")
		create_tables(engine)
		print("✅ All tables created successfully")
		
		# List created tables
		with engine.connect() as conn:
			result = conn.execute(text(
				"""
				SELECT table_name 
				FROM information_schema.tables 
				WHERE table_schema = 'public' 
				ORDER BY table_name
				"""
			))
			tables = [row[0] for row in result.fetchall()]
			print(f"📋 Created tables: {', '.join(tables)}")
		
		print("🎉 Database setup completed successfully!")
		return True
		
	except Exception as e:
		print(f"❌ Error setting up database: {e}")
		return False

if __name__ == "__main__":
	success = main()
	sys.exit(0 if success else 1)
