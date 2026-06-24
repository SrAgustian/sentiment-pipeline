import streamlit as st
import psycopg2
import os
import sys
from pathlib import Path

# Pastikan root project ada di PYTHONPATH agar modul lokal dapat diimport
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Import modules dari folder dashboard
from dashboard.style import apply_custom_css
from dashboard.tab_analytics import render_tab_analytics
from dashboard.tab_livetest import render_tab_livetest

# 1. Konfigurasi Halaman Utama (Wajib di baris pertama Streamlit)
st.set_page_config(
    page_title="Dashboard Sentimen E-Commerce",
    page_icon="📊",
    layout="wide"
)

# 2. Terapkan Jurus CSS
apply_custom_css()

# 3. Inisiasi Database Koneksi
@st.cache_resource 
def init_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "sentiment_db"),
        user=os.getenv("DB_USER", "sentiment_user"),
        password=os.getenv("DB_PASSWORD", "9a8b7c6d5e") 
    )

try:
    conn = init_connection()
except Exception as e:
    st.error(f"Gagal koneksi ke database: {e}")
    conn = None

# 4. Tampilkan Header
st.title("📊 Dashboard Analisis Sentimen Ulasan E-Commerce")
st.markdown("Automated Data Pipeline & MLOps System by **M. Shandy Agustian**")
st.markdown("---")

# 5. Render Tab Navigasi
tab1, tab2 = st.tabs(["📈 Analitik & Tren Sentimen", "🤖 Live Test Model ML"])

with tab1:
    render_tab_analytics(conn)

with tab2:
    render_tab_livetest()