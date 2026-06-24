import streamlit as st

def apply_custom_css():
    st.markdown("""
    <style>
        /* Desain Card untuk Metrik (KPI) */
        div[data-testid="metric-container"] {
            background-color: rgba(255, 255, 255, 0.05); /* Transparan elegan */
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 15px 20px;
            border-radius: 15px;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        /* Efek melayang saat mouse diarahkan ke kotak angka */
        div[data-testid="metric-container"]:hover {
            transform: translateY(-7px);
            box-shadow: 0px 8px 25px rgba(0,0,0,0.2);
            border-color: #4CAF50; /* Garis pinggir jadi hijau pas di-hover */
        }

        /* Menyembunyikan menu bawaan Streamlit (Garis tiga di kanan atas) */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)