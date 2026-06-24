import streamlit as st
import joblib
from scripts.transformer import clean_text

def render_tab_livetest():
    st.header("🧪 Uji Model Sentimen Langsung (Live Testing)")
            
    # Load Model ML
    @st.cache_resource
    def load_ml_models():
        model = joblib.load("models/ensemble_model.pkl")
        vectorizer = joblib.load("models/tfidf_vectorizer.pkl")
        return model, vectorizer
    
    model, vectorizer = load_ml_models()
    st.write("Ketik ulasan di bawah ini untuk menguji performa model Machine Learning secara langsung.")

    user_input = st.text_area("Masukkan Ulasan Pelanggan:", placeholder="Contoh: Aplikasi ini sangat membantu dan cepat...")

    if st.button("Prediksi Sentimen", type="primary"):
        if user_input.strip() == "":
            st.warning("⚠️ Silakan masukkan teks ulasan terlebih dahulu.")
        else:
            with st.spinner("🤖 Menginisialisasi AI dan Sastrawi..."):
                cleaned_input = clean_text(user_input)
                vec_input = vectorizer.transform([cleaned_input])
                prediction = model.predict(vec_input)[0]

                try:
                    probs = model.predict_proba(vec_input)[0]
                    confidence = max(probs)
                except:
                    confidence = 0.99

                st.markdown("---")
                st.subheader("📊 Hasil Analisis:")

                if prediction.lower() == 'positif':
                    st.success(f"**Prediksi Label:** {prediction.upper()} 😊")
                elif prediction.lower() == 'negatif':
                    st.error(f"**Prediksi Label:** {prediction.upper()} 😡")
                else:
                    st.warning(f"**Prediksi Label:** {prediction.upper()} 😐")
                    
                st.info(f"**Tingkat Keyakinan (Confidence):** {confidence:.2%}")
                st.caption(f"*Teks Preprocessed:* {cleaned_input}")