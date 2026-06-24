import os
import pandas as pd
import requests

# 1. Setup direktori penyimpanan
save_dir = 'data/dictionaries'
os.makedirs(save_dir, exist_ok=True)

print("🚀 Memulai proses setup dictionary...")

# =========================================================
# 2. GENERATE KAMUS SLANG / ALAY
# =========================================================
print("⏳ Membuat Kamus Slang E-commerce...")
slang_mapping = {
    "bgs": "bagus", "bgt": "banget", "apk": "aplikasi", "app": "aplikasi",
    "sy": "saya", "gx": "tidak", "gak": "tidak", "gk": "tidak", "ngga": "tidak",
    "nggak": "tidak", "tdk": "tidak", "dpt": "dapat", "krg": "kurang",
    "kcewa": "kecewa", "cpt": "cepat", "lmbt": "lambat", "lola": "lambat",
    "lemot": "lambat", "mantul": "mantap", "mantab": "mantap", "pake": "pakai",
    "bnyk": "banyak", "brg": "barang", "ongkir": "ongkos kirim", "cs": "customer service",
    "min": "admin", "minn": "admin", "pdhl": "padahal", "gaje": "tidak jelas",
    "gampang": "mudah", "nyusahin": "susah", "update": "perbarui",
    "tp": "tapi", "klo": "kalau", "kalo": "kalau", "sm": "sama", "dg": "dengan",
    "dgn": "dengan", "pd": "pada", "jg": "juga", "jgn": "jangan", "udh": "sudah",
    "sdh": "sudah", "blm": "belum", "dr": "dari", "aj": "saja", "aja": "saja"
}

# Convert ke DataFrame dan simpan
slang_df = pd.DataFrame(list(slang_mapping.items()), columns=['slang', 'formal'])
slang_path = os.path.join(save_dir, 'slang_dictionary.csv')
slang_df.to_csv(slang_path, index=False)
print(f"✅ Berhasil menyimpan Kamus Slang di: {slang_path}")


# =========================================================
# 3. DOWNLOAD INSET LEXICON DARI GITHUB
# =========================================================
# Kita ambil file .tsv original dari repositori fajri91
inset_urls = {
    "positive": "https://raw.githubusercontent.com/fajri91/InSet/master/positive.tsv",
    "negative": "https://raw.githubusercontent.com/fajri91/InSet/master/negative.tsv"
}

for sentiment, url in inset_urls.items():
    print(f"⏳ Mendownload InSet {sentiment.capitalize()}...")
    try:
        # Load TSV (Tab-Separated Values)
        df_inset = pd.read_csv(url, sep='\t')
        
        # Penyesuaian Header: Kadang file TSV asli tidak memiliki header yang standar
        # Kita paksakan 2 kolom pertama bernama 'word' dan 'weight' untuk Fase 3
        df_inset = df_inset.iloc[:, 0:2] # Ambil hanya 2 kolom pertama
        df_inset.columns = ['word', 'weight']
        
        # Drop nilai kosong jika ada
        df_inset = df_inset.dropna()
        
        # Simpan ke format CSV sesuai panduan panduan lo
        csv_path = os.path.join(save_dir, f'inset_{sentiment}.csv')
        df_inset.to_csv(csv_path, index=False)
        print(f"✅ Berhasil mengonversi dan menyimpan: {csv_path}")
        
    except Exception as e:
        print(f"❌ Gagal mendownload atau memproses {sentiment} lexicon: {e}")

print("\n🎉 SETUP SELESAI! Semua amunisi Fase 3 sudah siap di folder data/dictionaries/")