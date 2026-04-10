
import psycopg2
from config import settings

def test_conn():
    try:
        print(f"Attempting to connect to {settings.db_name} on {settings.db_host}:{settings.db_port}...")
        conn = psycopg2.connect(
            host=settings.db_host,
            database=settings.db_name,
            user=settings.db_user,
            password=settings.db_password,
            port=settings.db_port,
            connect_timeout=3
        )
        print("Connection successful!")
        conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_conn()
