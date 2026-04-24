"""
scripts/test_db_connection.py
Verifikasi koneksi Python → PostgreSQL berjalan normal.
Jalankan: python scripts/test_db_connection.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    try:
        import psycopg2
    except ImportError:
        print("❌  psycopg2 belum terinstall. Jalankan: pip install psycopg2-binary")
        sys.exit(1)

    config = {
        "host":     "localhost",
        "port":     5432,
        "dbname":   os.getenv("POSTGRES_DB",       "sentiment_db"),
        "user":     os.getenv("POSTGRES_USER",     "sentiment_user"),
        "password": os.getenv("POSTGRES_PASSWORD", ""),
    }

    print(f"🔌  Mencoba konek ke PostgreSQL...")
    print(f"    host={config['host']}  db={config['dbname']}  user={config['user']}")

    try:
        conn = psycopg2.connect(**config)
        cur  = conn.cursor()

        # ── Test INSERT ─────────────────────────────────────
        cur.execute("""
            INSERT INTO raw_reviews (app_name, review_text, rating, review_date)
            VALUES (%s, %s, %s, CURRENT_DATE)
            ON CONFLICT DO NOTHING
        """, ("test_app", "Ulasan uji coba koneksi database", 5))
        conn.commit()
        print("✅  INSERT berhasil")

        # ── Test SELECT ─────────────────────────────────────
        cur.execute("SELECT COUNT(*) FROM raw_reviews WHERE app_name = 'test_app'")
        count = cur.fetchone()[0]
        print(f"✅  SELECT berhasil — {count} baris ditemukan di raw_reviews")

        # ── Cek semua tabel ─────────────────────────────────
        cur.execute("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        tables = [row[0] for row in cur.fetchall()]
        print(f"✅  Tabel yang tersedia: {', '.join(tables)}")

        # ── Cleanup test data ────────────────────────────────
        cur.execute("DELETE FROM raw_reviews WHERE app_name = 'test_app'")
        conn.commit()
        print("✅  Cleanup data uji selesai")

        cur.close()
        conn.close()
        print("\n🎉  Koneksi PostgreSQL berfungsi normal. Fase 1 Task 6 ✓")

    except psycopg2.OperationalError as e:
        print(f"\n❌  Gagal konek: {e}")
        print("\nPastikan:")
        print("  1. Container Docker sudah berjalan  →  docker compose up -d")
        print("  2. File .env sudah diisi dengan benar")
        print("  3. Port 5432 tidak diblokir firewall")
        sys.exit(1)


if __name__ == "__main__":
    test_connection()
