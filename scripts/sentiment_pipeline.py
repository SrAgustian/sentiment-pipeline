import os
import re
import pickle
import pandas as pd
from collections import Counter

# NLP & ML Libraries
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.metrics import classification_report, accuracy_score
from imblearn.over_sampling import SMOTE

class SentimentPipeline:
    """
    Kelas OOP untuk Pipeline Sentimen Analisis MLOps.
    Mencakup: Preprocessing, Labeling (Lexicon), Feature Extraction, dan Training.
    """
    def __init__(self, base_path='.'):
        self.base_path = base_path
        print("⚙️ Inisialisasi Sentiment Pipeline...")
        
        # 1. Setup Sastrawi
        self.stemmer = StemmerFactory().create_stemmer()
        
        # 2. Setup Rules & Dictionaries
        self.kata_negasi = {'tidak', 'bukan', 'tak', 'jangan', 'belum', 'tanpa', 'enggak', 'ga', 'gak'}
        self.kata_abaikan = {'aplikasi', 'app', 'apk', 'shopee', 'tokopedia', 'blibli'}
        self.kamus_slang = {"bgt": "banget", "gak": "tidak", "blm": "belum", "nyusahin": "susah", "pdhl": "padahal"}
        
        # 3. Load InSet Lexicon
        pos_lex = pd.read_csv(os.path.join(base_path, 'data/dictionaries/inset_positive.csv'))
        neg_lex = pd.read_csv(os.path.join(base_path, 'data/dictionaries/inset_negative.csv'))
        
        self.pos_dict = {str(w).strip(): int(wt) for w, wt in zip(pos_lex['word'], pos_lex['weight']) if pd.notna(w)}
        self.neg_dict = {str(w).strip(): int(wt) for w, wt in zip(neg_lex['word'], neg_lex['weight']) if pd.notna(w)}
        
        # 4. Setup Model Machine Learning
        self.vectorizer = TfidfVectorizer(max_features=5000)
        nb = MultinomialNB()
        rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        self.model = VotingClassifier(estimators=[('Naive Bayes', nb), ('Random Forest', rf)], voting='soft')

    def preprocess_text(self, text):
        """Fungsi membersihkan teks."""
        if pd.isna(text): return ""
        text = str(text).lower()
        text = re.sub(r'http\S+|www\S+', '', text)
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        
        words = text.split()
        words = [self.kamus_slang.get(w, w) for w in words]
        
        clean_text = ' '.join(words)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        return self.stemmer.stem(clean_text)

    def label_sentiment(self, text):
        """Fungsi pelabelan berbasis Lexicon dengan Negation Handling."""
        if pd.isna(text) or text == "": return 'Netral'
        tokens = str(text).split()
        score = 0
        
        for i, token in enumerate(tokens):
            if token in self.kata_abaikan: continue
            
            word_score = 0
            if token in self.pos_dict: word_score = self.pos_dict[token]
            elif token in self.neg_dict: word_score = self.neg_dict[token]
            
            # Flip score jika ada kata negasi sebelumnya
            if i > 0 and tokens[i-1] in self.kata_negasi:
                word_score *= -1
                
            score += word_score
            
        if score > 0: return 'Positif'
        elif score < 0: return 'Negatif'
        else: return 'Netral'

    def train_model(self, df):
        """Fungsi end-to-step untuk merubah teks jadi fitur, SMOTE, dan melatih model."""
        print("🚀 Memulai proses Training Model MLOps...")
        
        # Ekstraksi Fitur
        X = self.vectorizer.fit_transform(df['clean_text'])
        y = df['label']
        
        # Train-Test Split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        
        # Terapkan SMOTE
        print("   -> Menerapkan SMOTE untuk menyeimbangkan data...")
        smote = SMOTE(random_state=42)
        X_train_smote, y_train_smote = smote.fit_resample(X_train, y_train)
        
        # Training
        print("   -> Melatih Ensemble Model (Naive Bayes + Random Forest)...")
        self.model.fit(X_train_smote, y_train_smote)
        
        # Evaluasi
        print("\n🏆 HASIL EVALUASI MODEL:")
        y_pred = self.model.predict(X_test)
        print(f"Akurasi Keseluruhan: {accuracy_score(y_test, y_pred):.4f}")
        print(classification_report(y_test, y_pred))

    def save_artifacts(self):
        """Fungsi untuk menyimpan model dan vectorizer ke file .pkl"""
        model_path = os.path.join(self.base_path, 'models', 'ensemble_model.pkl')
        vec_path = os.path.join(self.base_path, 'models', 'tfidf_vectorizer.pkl')
        
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        with open(vec_path, 'wb') as f:
            pickle.dump(self.vectorizer, f)
            
        print(f"✅ Model berhasil disimpan di: {model_path}")
        print(f"✅ Vectorizer berhasil disimpan di: {vec_path}")

# ==========================================
# BLOK PENGUJIAN (Akan jalan jika script ini dieksekusi langsung)
# ==========================================
if __name__ == "__main__":
    # Tentukan path (Mundur satu langkah jika dijalankan dari dalam folder src)
    BASE_DIR = '../' if os.path.basename(os.getcwd()) == 'scripts' else './'
    
    # 1. Inisialisasi Class
    pipeline = SentimentPipeline(base_path=BASE_DIR)
    
    # 2. Buka data yang sudah kita bersihkan di Notebook tadi (Contoh: Shopee)
    data_path = os.path.join(BASE_DIR, 'data', 'processed', 'clean_shopee.csv')
    if os.path.exists(data_path):
        print(f"\n📦 Memuat data dari: {data_path}")
        df_shopee = pd.read_csv(data_path)
        
        # 3. Latih Model
        pipeline.train_model(df_shopee)
        
        # 4. Simpan Otak AI-nya ke folder 'models'
        pipeline.save_artifacts()
    else:
        print(f"❌ File tidak ditemukan di {data_path}. Pastikan path benar!")