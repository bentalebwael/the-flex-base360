
import os
import sys

# Add /app to python path to emulate running from root
sys.path.append('/app')

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    print("✅ psycopg2 imported successfully")
except ImportError as e:
    print(f"❌ Failed to import psycopg2: {e}")
    sys.exit(1)

try:
    from app.config import settings
    print(f"✅ Settings loaded. Database URL: {settings.database_url}")
except ImportError as e:
    print(f"❌ Failed to import settings: {e}")
    sys.exit(1)

try:
    print(f"Attempting connection to {settings.database_url}...")
    conn = psycopg2.connect(settings.database_url)
    print("✅ Connection established")
    
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, name, tenant_id FROM properties LIMIT 5")
    rows = cur.fetchall()
    
    print(f"✅ Query successful. Found {len(rows)} rows:")
    for row in rows:
        print(row)
        
    conn.close()
except Exception as e:
    print(f"❌ Database connection/query failed: {e}")
    sys.exit(1)
