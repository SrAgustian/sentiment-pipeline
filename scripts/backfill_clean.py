import pandas as pd
import psycopg2
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(message)s')

# Konfigurasi Database (Mengetuk pintu Docker via localhost)
DB_CONFIG = {
    "dbname": "sentiment_db", 
    "user": "sentiment_user",
    "password": "9a8b7c6d5e", 
    "host": "127.0.0.1",
    "port": "5432"
}

# Lokasi File CSV Bersih
CSV_FILES = [
    '../data/processed/clean_tokopedia.csv',
    '../data/processed/clean_shopee.csv',
    '../data/processed/clean_blibli.csv'
]

def parse_indo_date(date_str):
    """Fallback pengubah tanggal jika format masih Indo"""
    months = {
        "Januari": "01", "Februari": "02", "Maret": "03", "April": "04",
        "Mei": "05", "Juni": "06", "Juli": "07", "Agustus": "08",
        "September": "09", "Oktober": "10", "November": "11", "Desember": "12"
    }
    try:
        # Coba parse dengan pandas dulu (kalau sudah YYYY-MM-DD)
        return pd.to_datetime(date_str).strftime('%Y-%m-%d')
    except:
        try:
            parts = str(date_str).split()
            if len(parts) == 3:
                day, month_name, year = parts
                return f"{year}-{months.get(month_name, '01')}-{day.zfill(2)}"
        except:
            return None

def run_backfill():
    conn = psycopg2.connect(**DB_CONFIG)
    
    for file_path in CSV_FILES:
        if not os.path.exists(file_path):
            logging.warning(f"⚠️ File tidak ditemukan: {file_path}")
            continue
            
        logging.info(f"🚀 Membaca file: {os.path.basename(file_path)}")
        df = pd.read_csv(file_path)
        
        # Buang data yang kosong
        df = df.dropna(subset=['text', 'clean_text', 'label'])
        data_list = df.to_dict(orient='records')
        
        sukses_masuk = 0
        cursor = conn.cursor()
        
        for row in data_list:
            app = row['app']
            text = row['text']
            rating = row['rating']
            date = parse_indo_date(row['date'])
            scraped_at = row['scraped_at']
            clean_text = row['clean_text']
            # PENTING: Samakan huruf kapital sesuai constraint database ('Positif', 'Negatif', 'Netral')
            label = str(row['label']).capitalize() 
            
            # 1. Coba Insert ke raw_reviews, jika duplikat ambil ID-nya
            cursor.execute("""
                INSERT INTO raw_reviews (app_name, review_text, rating, review_date, scraped_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (app_name, review_date, review_text) DO NOTHING
                RETURNING id;
            """, (app, text, rating, date, scraped_at))
            
            res = cursor.fetchone()
            if res:
                raw_id = res[0]
            else:
                # Kalau duplicate (sudah ada), cari ID-nya
                cursor.execute("SELECT id FROM raw_reviews WHERE app_name=%s AND review_date=%s AND review_text=%s", (app, date, text))
                existing = cursor.fetchone()
                if not existing:
                    continue
                raw_id = existing[0]

            # 2. Insert ke processed_reviews (Cek dulu biar nggak duplikat)
            cursor.execute("SELECT id FROM processed_reviews WHERE raw_id=%s", (raw_id,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO processed_reviews (raw_id, cleaned_text)
                    VALUES (%s, %s);
                """, (raw_id, clean_text))

            # 3. Insert ke sentiment_results (Cek dulu biar nggak duplikat)
            cursor.execute("SELECT id FROM sentiment_results WHERE raw_id=%s", (raw_id,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO sentiment_results (raw_id, app_name, sentiment_label, confidence)
                    VALUES (%s, %s, %s, %s);
                """, (raw_id, app, label, None)) # Confidence diisi None karena hasil labeling lexicon lama
                
            sukses_masuk += 1
            
        conn.commit()
        cursor.close()
        logging.info(f"✅ Selesai! Berhasil memetakan {sukses_masuk} data dari {app.upper()}.\n")

    conn.close()

if __name__ == "__main__":
    run_backfill()