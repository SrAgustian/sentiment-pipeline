import pandas as pd
import joblib
import logging
import re
import json
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Inisialisasi Sastrawi
logging.info("Inisialisasi Sastrawi Stemmer ...")
factory = StemmerFactory()
stemmer = factory.create_stemmer()

# Konfigurasi path model
MODEL_PATH = "models/ensemble_model.pkl"
VECTORIZER_PATH = "models/tfidf_vectorizer.pkl"
MODEL_VER = "v1.0.0"

def convert_indo_date(date_str):
    """Mengubah format tanggal Google Play Store menjadi 'YYYY-MM-DD' untuk PostgreSQL."""
    if not date_str:
        return datetime.now().strftime("%Y-%m-%d")
        
    months = {
        "januari": "01", "februari": "02", "maret": "03", "april": "04",
        "mei": "05", "juni": "06", "juli": "07", "agustus": "08",
        "september": "09", "oktober": "10", "november": "11", "desember": "12",
        "jan": "01", "feb": "02", "mar": "03", "apr": "04", "mei": "05", "jun": "06",
        "jul": "07", "agu": "08", "sep": "09", "okt": "10", "nov": "11", "des": "12"
    }
    
    try:
        # Jika formatnya sudah YYYY-MM-DD (misal dari mock data), langsung kembalikan
        if re.match(r'^\d{4}-\d{2}-\d{2}$', str(date_str)):
            return str(date_str)
            
        parts = str(date_str).lower().split()
        if len(parts) >= 3:
            day = parts[0].zfill(2)
            month = months.get(parts[1], "01")
            year = parts[2]
            return f"{year}-{month}-{day}"
    except Exception as e:
        logging.warning(f"Gagal memparsing tanggal '{date_str}': {e}")
        
    return datetime.now().strftime("%Y-%m-%d")

def clean_text(text):
    """Pembersihan dasar dan stemming menggunakan Sastrawi."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)
    text = stemmer.stem(text)
    return text

def run_transform(raw_data: list) -> str:
    """
    Fungsi utama yang akan dipanggil oleh task Airflow.
    Input: list of dictionary dari extractor XCom
    Output: JSON string untuk loader
    """
    logging.info(f"Memulai transformasi untuk {len(raw_data)} baris data.")
    
    if not raw_data:
        logging.warning("Data kosong! Mengembalikan JSON string kosong.")
        return "[]"
    
    # 1. Load model & vectorizer
    try:
        logging.info("Memuat model ML dari disk...")
        model = joblib.load(MODEL_PATH)
        vectorizer = joblib.load(VECTORIZER_PATH)
    except Exception as e:
        logging.error(f"Gagal memuat file .pkl: {e}")
        raise e

    # 2. Konversi ke DataFrame
    df = pd.DataFrame(raw_data)
    
    # 3. Preprocessing menggunakan kolom 'review_text' hasil extractor baru
    logging.info("Mulai membersihkan teks dan stemming ...")
    df['clean_text'] = df['review_text'].apply(clean_text)
    
    # Hapus baris kosong
    df = df[df['clean_text'].str.strip() != ""]
    
    if df.empty:
        logging.warning("DataFrame kosong setelah proses pembersihan teks.")
        return "[]"
        
    # 4. Vektorisasi & Prediksi
    logging.info("Melakukan vektorisasi TF-IDF dan Prediksi...")
    X = vectorizer.transform(df['clean_text'])
    df['label'] = model.predict(X)
    
    try:
        probs = model.predict_proba(X)
        df['confidence'] = probs.max(axis=1)
    except:
        df['confidence'] = 0.99 
        
    # 5. Penyelarasan format tanggal dan versi model
    df['review_date'] = df['review_date'].apply(convert_indo_date)
    df['model_ver'] = MODEL_VER
    
    logging.info("Transformasi berhasil diselesaikan.")
    
    # Return JSON records string
    return df.to_json(orient='records')

if __name__ == "__main__":
    print("=== TESTING MANUAL TRANSFORMER ===")
    mock_data = [
        {
            "app_name": "tokopedia",
            "review_text": "Aplikasi ini sangat bagus dan pengirimannya cepat!",
            "rating": 5,
            "review_date": "10 Mei 2026",
            "scraped_at": "2026-06-10 01:00:00"
        }
    ]
    hasil_json = run_transform(mock_data)
    print(f"Hasil output JSON:\n{hasil_json}")