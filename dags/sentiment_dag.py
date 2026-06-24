from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os
import json

# Menambahkan folder utama project ke dalam path agar Airflow bisa membaca folder 'scripts'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.extractor import run_extract
from scripts.transformer import run_transform
from scripts.loader import run_load

# Aturan standar untuk "Mandor" Airflow
default_args = {
    'owner': 'shandy',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# --- WRAPPER FUNCTIONS UNTUK AIRFLOW TASK ---

def extract_task_wrapper(**kwargs):
    app_name = kwargs['app_name']
    print(f"Memulai ekstraksi mingguan untuk: {app_name}")
    # Narik 500 ulasan biar terbukti datanya nambah di Dashboard!
    data = run_extract(app_name=app_name, n_reviews=500) 
    return data 

def transform_task_wrapper(**kwargs):
    ti = kwargs['ti']
    app_name = kwargs['app_name']
    
    raw_data = ti.xcom_pull(task_ids=f"extract_{app_name}")
    
    if not raw_data:
        print("Data kosong, tidak ada yang perlu di-transform.")
        return "[]"
        
    json_data = run_transform(raw_data)
    return json_data 

def load_task_wrapper(**kwargs):
    ti = kwargs['ti']
    app_name = kwargs['app_name']
    
    json_data_str = ti.xcom_pull(task_ids=f"transform_{app_name}")
    data_list = json.loads(json_data_str)
    
    print(f"Menjalankan Load: Mengirim {len(data_list)} baris data hasil prediksi ke PostgreSQL...")
    inserted_rows = run_load(data_list) 
    print(f"Task Load Berhasil! {inserted_rows} data baru ditambahkan ke database.")

# --- DEFINISI DAG UTAMA ---

with DAG(
    'sentiment_pipeline_v2', # <--- Nama KTP baru: V2
    default_args=default_args,
    description='Pipeline Otomatis Skripsi Shandy - Full ETL Terintegrasi',
    schedule_interval='@weekly', 
    start_date=datetime(2026, 5, 1),
    catchup=False,
) as dag:

    # 🚀 JALANKAN 3 APLIKASI SEKALIGUS
    target_apps = ['tokopedia', 'shopee', 'blibli']

    for app in target_apps:
        task_extract = PythonOperator(
            task_id=f'extract_{app}',
            python_callable=extract_task_wrapper,
            op_kwargs={'app_name': app},
        )

        task_transform = PythonOperator(
            task_id=f'transform_{app}',
            python_callable=transform_task_wrapper,
            op_kwargs={'app_name': app},
        )

        task_load = PythonOperator(
            task_id=f'load_{app}',
            python_callable=load_task_wrapper,
            op_kwargs={'app_name': app},
        )

        # Alur Kerja untuk masing-masing aplikasi
        task_extract >> task_transform >> task_load