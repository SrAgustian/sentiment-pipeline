import pandas as pd
import json
import logging
import os
from scripts.transformer import run_transform
from scripts.loader import run_load

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    backup_file = 'backup_transformed_30k.json'
    
    # CEK SABUK PENGAMAN: Kalau file backup udah ada, LANGSUNG LOAD JSON-nya! Gak usah nunggu 1 jam!
    if os.path.exists(backup_file):
        logging.info(f"🌟 DATA BACKUP DITEMUKAN ({backup_file})!")
        logging.info("Melewati proses Sastrawi & Prediksi, langsung mengeksekusi Load ke Database...")
        with open(backup_file, 'r', encoding='utf-8') as f:
            data_list = json.load(f)
            
    else:
        # KALAU BELUM ADA BACKUP, BACA CSV & TRANSFORM DARI AWAL
        csv_files = [
            'data/raw/raw_tokopedia.csv',
            'data/raw/raw_shopee.csv',
            'data/raw/raw_blibli.csv'
        ]
        
        all_raw_data = []
        for file in csv_files:
            if os.path.exists(file):
                try:
                    df = pd.read_csv(file)
                    records = df.to_dict('records')
                    all_raw_data.extend(records)
                    logging.info(f"✅ Berhasil membaca {len(records)} baris dari {file}")
                except Exception as e:
                    logging.error(f"❌ Gagal membaca {file}: {e}")
            else:
                logging.warning(f"⚠️ File {file} tidak ditemukan!")

        if not all_raw_data:
            logging.error("Tidak ada data. Henti.")
            return

        logging.info(f"🔥 Total data mentah terkumpul: {len(all_raw_data)} baris.")
        logging.info("🧠 Memulai proses Transform & Predict... Silakan ngopi 1 jam!")
        
        json_data_str = run_transform(all_raw_data)
        data_list = json.loads(json_data_str)
        
        # --- SABUK PENGAMAN DIBUAT DISINI ---
        logging.info("💾 Menyimpan hasil transformasi ke BACKUP JSON agar aman...")
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(data_list, f)
        logging.info("✅ Backup JSON berhasil dibuat!")
    
    # 3. Load ke Database
    logging.info(f"✨ Mempersiapkan Load {len(data_list)} data ke PostgreSQL...")
    inserted_rows = run_load(data_list)
    logging.info(f"🎉 THE GRAND BACKFILL SELESAI! {inserted_rows} data sukses masuk ke PostgreSQL.")

if __name__ == "__main__":
    main()