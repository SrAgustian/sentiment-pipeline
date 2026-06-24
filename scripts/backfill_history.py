import pandas as pd
import joblib
from sqlalchemy import create_engine, text
import re
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
import time

# ==========================================
# 1. KONFIGURASI DATABASE
# ==========================================
DB_USER = 'sentiment_user' 
DB_PASS = '9a8b7c6d5e'
DB_HOST = '127.0.0.1' 
DB_PORT = '5432'
DB_NAME = 'sentiment_db'

CSV_FILES = [
    {'app': 'tokopedia', 'path': '../data/raw/raw_tokopedia.csv'},
    {'app': 'shopee', 'path': '../data/raw/raw_shopee.csv'},
    {'app': 'blibli', 'path': '../data/raw/raw_blibli.csv'}
]
MODEL_PATH = '../models/ensemble_model.pkl'

engine = create_engine(f'postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

# ==========================================
# 2. INISIALISASI
# ==========================================
print("⏳ Memuat model ML & Stemmer...")
model = joblib.load(MODEL_PATH)
stemmer = StemmerFactory().create_stemmer()

def parse_indo_date(date_str):
    """Mengubah format 'DD NamaBulan YYYY' ke 'YYYY-MM-DD'"""
    months = {
        "Januari": "01", "Februari": "02", "Maret": "03", "April": "04",
        "Mei": "05", "Juni": "06", "Juli": "07", "Agustus": "08",
        "September": "09", "Oktober": "10", "November": "11", "Desember": "12"
    }
    try:
        parts = str(date_str).split()
        if len(parts) == 3:
            day, month_name, year = parts
            return f"{year}-{months.get(month_name, '01')}-{day.zfill(2)}"
        return None
    except:
        return None

# ==========================================
# 3. FUNGSI UPSERT
# ==========================================
def upsert_to_db(df, table_name, engine):
    """Memasukkan data, mengabaikan duplikat berdasarkan app, date, dan text."""
    data = df.to_dict(orient='records')
    # Gunakan SQL mentah untuk upsert yang lebih aman
    sql = text(f"""
        INSERT INTO {table_name} (app_name, review_text, rating, review_date, scraped_at)
        VALUES (:app_name, :review_text, :rating, :review_date, :scraped_at)
        ON CONFLICT (app_name, review_date, review_text) 
        DO NOTHING;
    """)
    with engine.begin() as conn:
        for row in data:
            conn.execute(sql, row)

# ==========================================
# 4. PROSES EKSEKUSI
# ==========================================
def run_backfill():
    for file_info in CSV_FILES:
        app_name = file_info['app']
        file_path = file_info['path']
        
        print(f"\n🚀 Memulai backfill: {app_name.upper()}")
        try:
            df = pd.read_csv(file_path)
            
            # Bersihkan dan siapkan dataframe
            raw_df = pd.DataFrame({
                'app_name': df['app'],
                'review_text': df['text'],
                'rating': df['rating'],
                'review_date': df['date'].apply(parse_indo_date),
                'scraped_at': df['scraped_at']
            })
            
            # Load ke DB
            upsert_to_db(raw_df, 'raw_reviews', engine)
            print(f"✅ Data {app_name} berhasil di-load!")
            
        except Exception as e:
            print(f"❌ Error pada {app_name}: {e}")

if __name__ == "__main__":
    run_backfill()