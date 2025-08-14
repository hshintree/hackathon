from database.storage import DataStorage
from sqlalchemy import text

def test_database_connection():
    try:
        s = DataStorage()
        with s.get_session() as db:
            result = db.execute(text('SELECT 1 as test')).fetchone()
            print('Database connection successful:', result)
            
            tables_result = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
            print('Available tables:', [row[0] for row in tables_result])
            
            try:
                market_data_count = db.execute(text("SELECT COUNT(*) FROM market_data")).fetchone()
                print('Market data rows:', market_data_count[0] if market_data_count else 0)
            except Exception as e:
                print('Market data table not accessible:', str(e))
            
    except Exception as e:
        print('Database connection failed:', str(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database_connection()
