import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from wordcloud import WordCloud

def render_tab_analytics(conn):
    st.header("📈 Metrik Utama & Tren Temporal")
    
    if not conn:
        st.error("Gagal memuat visualisasi karena database tidak terkoneksi.")
        return

    # 1. Tarik Data dari DB
    @st.cache_data(ttl=60)
    def load_dashboard_data():
        try:
            conn.rollback()
        except:
            pass
            
        # 👇 PERBAIKAN QUERY SQL SESUAI SKEMA DATABASE DOCKER LO 👇
        query = """
            SELECT 
                r.review_date, 
                r.rating, 
                r.app_name, 
                p.cleaned_text AS clean_text, 
                s.sentiment_label AS sentiment
            FROM raw_reviews r
            JOIN processed_reviews p ON r.id = p.raw_id
            JOIN sentiment_results s ON r.id = s.raw_id;
        """
        df = pd.read_sql(query, conn)
        df['review_date'] = pd.to_datetime(df['review_date'])
        return df
        
    df_raw = load_dashboard_data()
    df_raw['sentiment'] = df_raw['sentiment'].astype(str).str.lower()
    
    # Ekstrak Tahun dari review_date untuk filter
    df_raw['Tahun'] = df_raw['review_date'].dt.year.astype(int)

    # ==========================================
    # 2. FILTER DATA (DI HALAMAN UTAMA BUKAN SIDEBAR)
    # ==========================================
    st.markdown("##### 🔍 Filter Data")
    
    col_f1, col_f2 = st.columns(2) # Bagi jadi 2 kolom sejajar
    
    with col_f1:
        daftar_aplikasi = ["Semua Aplikasi"] + list(df_raw['app_name'].unique())
        pilihan_app = st.selectbox("📊 Pilih Aplikasi:", daftar_aplikasi)

    with col_f2:
        daftar_tahun = ["Semua Tahun"] + sorted(list(df_raw['Tahun'].unique()), reverse=True)
        pilihan_tahun = st.selectbox("📅 Pilih Tahun:", daftar_tahun)

    # Terapkan Logika Filter Ganda
    df_reviews = df_raw.copy()
    
    if pilihan_app != "Semua Aplikasi":
        df_reviews = df_reviews[df_reviews['app_name'] == pilihan_app]
        
    if pilihan_tahun != "Semua Tahun":
        df_reviews = df_reviews[df_reviews['Tahun'] == pilihan_tahun]
    
    st.markdown("<br>", unsafe_allow_html=True) # Jeda spasi sedikit
    # ==========================================

    # 3. Hitung Metrik Utama
    total_data = len(df_reviews)
    positif_count = len(df_reviews[df_reviews['sentiment'] == 'positif'])
    negatif_count = len(df_reviews[df_reviews['sentiment'] == 'negatif'])

    pct_pos = (positif_count / total_data) * 100 if total_data > 0 else 0
    pct_neg = (negatif_count / total_data) * 100 if total_data > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("📊 Total Ulasan", f"{total_data:,}")
    col2.metric("🟢 Ulasan Puas", f"{positif_count:,}", f"{pct_pos:.1f}%")
    col3.metric("🔴 Ulasan Kecewa", f"{negatif_count:,}", f"{pct_neg:.1f}%")
    st.markdown("---")

    # 4. Grafik Tren
    st.subheader("🗓️ Grafik Tren Sentimen Bulanan")
    df_trend_source = df_reviews.copy()
    df_trend_source['Bulan'] = df_trend_source['review_date'].dt.to_period('M').astype(str)
    df_trend = df_trend_source.groupby(['Bulan', 'sentiment']).size().reset_index(name='Jumlah')

    # Buat Judul Dinamis
    judul_tren = f"Tren Kepuasan Pengguna - {pilihan_app} ({pilihan_tahun})"
    
    fig_line = px.line(
        df_trend, x='Bulan', y='Jumlah', color='sentiment',
        color_discrete_map={'positif': '#2ca02c', 'negatif': '#d62728', 'netral': '#1f77b4'},
        markers=True, title=judul_tren
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # 5. Grafik Distribusi Aplikasi
    st.subheader("🏪 Distribusi Ulasan per Aplikasi E-Commerce")
    df_app = df_reviews.groupby(['app_name', 'sentiment']).size().reset_index(name='Jumlah')
    fig_bar = px.bar(
        df_app, x='app_name', y='Jumlah', color='sentiment', barmode='group',
        color_discrete_map={'positif': '#2ca02c', 'negatif': '#d62728', 'netral': '#1f77b4'},
        labels={'app_name': 'Nama Aplikasi'}
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # ==========================================
    # ☁️ 6. FITUR BARU: WORD CLOUD (AWAN KATA)
    # ==========================================
    st.markdown("---")
    st.subheader("☁️ Kata Paling Sering Muncul (Word Cloud)")
    
    df_pos = df_reviews[df_reviews['sentiment'] == 'positif']
    df_neg = df_reviews[df_reviews['sentiment'] == 'negatif']

    col_wc1, col_wc2 = st.columns(2)

    with col_wc1:
        st.markdown("<h5 style='text-align: center; color: #2ca02c;'>Dominasi Kata: Puas 😊</h5>", unsafe_allow_html=True)
        if not df_pos.empty:
            text_pos = " ".join(df_pos['clean_text'].dropna())
            wc_pos = WordCloud(width=800, height=400, background_color='white', colormap='Greens', max_words=100).generate(text_pos)
            fig_pos, ax_pos = plt.subplots(figsize=(8, 4))
            ax_pos.imshow(wc_pos, interpolation='bilinear')
            ax_pos.axis('off') 
            st.pyplot(fig_pos)
        else:
            st.info("Data ulasan positif kosong.")

    with col_wc2:
        st.markdown("<h5 style='text-align: center; color: #d62728;'>Dominasi Kata: Kecewa 😡</h5>", unsafe_allow_html=True)
        if not df_neg.empty:
            text_neg = " ".join(df_neg['clean_text'].dropna())
            wc_neg = WordCloud(width=800, height=400, background_color='white', colormap='Reds', max_words=100).generate(text_neg)
            fig_neg, ax_neg = plt.subplots(figsize=(8, 4))
            ax_neg.imshow(wc_neg, interpolation='bilinear')
            ax_neg.axis('off') 
            st.pyplot(fig_neg)
        else:
            st.info("Data ulasan negatif kosong.")