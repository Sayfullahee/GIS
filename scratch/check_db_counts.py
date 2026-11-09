import psycopg2

conn = psycopg2.connect(
    host='localhost', 
    port=5433, 
    dbname='fewcam', 
    user='fewcam_dev', 
    password='ZFTLsRHDsOr8-zKSJLQcnLuitP4jebUoWCAaIeW9mfejDquF'
)
cur = conn.cursor()

schemas = ['lookups', 'clean', 'derived', 'audit']
for schema in schemas:
    print(f"\n--- SCHEMA: {schema} ---")
    cur.execute(f"SELECT tablename FROM pg_tables WHERE schemaname = '{schema}' ORDER BY tablename;")
    tables = [r[0] for r in cur.fetchall()]
    for t in tables:
        cur.execute(f'SELECT count(*) FROM "{schema}"."{t}";')
        print(f'{t:32}: {cur.fetchone()[0]} rows')

conn.close()
