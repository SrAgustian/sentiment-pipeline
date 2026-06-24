import psycopg2
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Konfigurasi koneksi ke PostgreSQL
DB_CONFIG = {
    "dbname": "sentiment_db", 
    "user": "sentiment_user",
    "password": "9a8b7c6d5e", 
    "host": "sentiment_postgres",
    "port": "5432"
}

def get_db_connection():
    """Membuat koneksi ke database PostgreSQL."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logging.error(f"Gagal terkoneksi ke database: {e}")
        raise e

def run_load(data_list: list) -> int:
    """Fungsi utama untuk memasukkan data ke dalam 3 tabel secara berurutan."""
    if not data_list:
        logging.warning("Data kosong, tidak ada yang perlu di-load ke database.")
        return 0

    logging.info(f"Memulai proses load {len(data_list)} baris data ke PostgreSQL...")
    conn = None
    inserted_count = 0

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        for row in data_list:
            # 1. Insert ke tabel raw_reviews (Tabel Induk)
            cursor.execute("""
                INSERT INTO raw_reviews (app_name, review_text, rating, review_date, scraped_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (app_name, review_date, review_text) DO NOTHING
                RETURNING id;
            """, (
                row['app_name'], row['review_text'], row['rating'], 
                row['review_date'], row['scraped_at']
            ))
            
            result = cursor.fetchone()
            
            # Kalau result ada isinya, berarti ini data BARU. Lanjut ke tabel anak.
            if result:
                raw_id = result[0]

                # 2. Insert ke tabel processed_reviews (Sesuai init_db.sql: cleaned_text)
                cursor.execute("""
                    INSERT INTO processed_reviews (raw_id, cleaned_text)
                    VALUES (%s, %s);
                """, (raw_id, row['clean_text']))

                # 3. Insert ke tabel sentiment_results (Sesuai init_db.sql)
                # Pakai raw_id, app_name, sentiment_label, confidence
                cursor.execute("""
                    INSERT INTO sentiment_results (raw_id, app_name, sentiment_label, confidence)
                    VALUES (%s, %s, %s, %s);
                """, (raw_id, row['app_name'], row['label'], row['confidence']))
                
                inserted_count += 1

        # Commit semua transaksi ke database
        conn.commit()
        logging.info(f"Proses Load Selesai! Ada {inserted_count} data BARU yang berhasil disimpan.")

    except Exception as e:
        logging.error(f"Terjadi kesalahan saat load ke database: {e}")
        if conn:
            conn.rollback() # Batalkan semua kalau ada yang error
        raise e
    finally:
        if conn:
            cursor.close()
            conn.close()
            
    return inserted_count