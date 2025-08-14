try:
    import psycopg2
    print("✅ psycopg2 is available")
    
    from database.schema import get_database_url
    db_url = get_database_url()
    print(f"Database URL: {db_url}")
    
    import psycopg2
    from urllib.parse import urlparse
    parsed = urlparse(db_url)
    
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port,
        database=parsed.path[1:],  # Remove leading slash
        user=parsed.username,
        password=parsed.password
    )
    print("✅ Database connection successful")
    conn.close()
    
except ImportError as e:
    print(f"❌ psycopg2 not available: {e}")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
