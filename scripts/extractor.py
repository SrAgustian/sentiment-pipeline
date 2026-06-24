import os
os.environ['WDM_SSL_VERIFY'] = '0'
import time
import random
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from webdriver_manager.chrome import ChromeDriverManager

# Setup logging supaya jejaknya kebaca jelas di UI Airflow nanti
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

APP_URLS = {
    "shopee"    : "https://play.google.com/store/apps/details?id=com.shopee.id&hl=id",
    "tokopedia" : "https://play.google.com/store/apps/details?id=com.tokopedia.tkpd&hl=id",
    "blibli"    : "https://play.google.com/store/apps/details?id=blibli.mobile.commerce&hl=id"
}

def init_driver():
    """Setup browser Selenium. WAJIB headless untuk Airflow."""
    options = Options()
    options.add_argument("--headless=new") # WAJIB untuk Airflow
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    # 👇👇👇 VAKSIN ANTI-BUG WEBDRIVER MANAGER 👇👇👇
    driver_path = ChromeDriverManager().install()
    
    if "THIRD_PARTY_NOTICES" in driver_path or "LICENSE" in driver_path:
        dir_name = os.path.dirname(driver_path)
        driver_path = os.path.join(dir_name, "chromedriver")
        os.chmod(driver_path, 0o755) # Paksa file menjadi executable (Bisa dijalanin di Linux)
    # 👆👆👆 =================================== 👆👆👆

    driver = webdriver.Chrome(service=Service(driver_path), options=options)
    return driver

def scroll_and_load(driver, target_count):
    """Fungsi untuk scroll dan meload ulasan."""
    logging.info("Mencari tombol 'Lihat semua ulasan'...")
    try:
        see_all_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Lihat semua') or contains(text(),'See all')]"))
        )
        see_all_btn.click()
        logging.info("Tombol berhasil diklik! Kotak ulasan terbuka.")
        time.sleep(3)
    except Exception as e:
        logging.warning("Tombol tidak ditemukan atau sudah terbuka.")
    
    logging.info(f"Mulai scrolling untuk mencapai target {target_count} ulasan...")
    prev_count = 0
    stall_limit = 5 
    stall = 0
    
    while True:
        reviews = driver.find_elements(By.CSS_SELECTOR, 'div[class*="RHo1pe"]')
        current_count = len(reviews)
        logging.info(f"Ter-load: {current_count} ulasan")
        
        if current_count >= target_count:
            logging.info(f"Target {target_count} tercapai!")
            break
        
        if current_count == prev_count:
            stall += 1
            if stall >= stall_limit:
                logging.warning("Tidak ada ulasan baru yang ter-load. Berhenti scroll.")
                break
        else:
            stall = 0
        
        prev_count = current_count
        
        if len(reviews) > 0:
            last_review = reviews[-1]
            try:
                ActionChains(driver).move_to_element(last_review).perform()
                time.sleep(0.5)
                scroll_origin = ScrollOrigin.from_element(last_review)
                ActionChains(driver).scroll_from_origin(scroll_origin, 0, 5000).perform()
            except Exception as e:
                driver.execute_script("arguments[0].scrollIntoView(true);", last_review)
            
        time.sleep(random.uniform(3, 5))
        
    return driver.find_elements(By.CSS_SELECTOR, 'div[class*="RHo1pe"]')

def parse_reviews(review_elements, app_name):
    """Mengekstrak teks, rating, dan tanggal dari elemen."""
    reviews_data = []
    logging.info("Mulai mengekstrak data ulasan...")
    for container in review_elements:
        try:
            try:
                text = container.find_element(By.CSS_SELECTOR, 'div.h3YV2d').text.strip()
            except:
                text = ""
            
            try:
                rating_el = container.find_element(By.CSS_SELECTOR, 'div[role="img"][aria-label]')
                aria = rating_el.get_attribute("aria-label")
                rating = int(aria.split()[2])
            except:
                rating = None
            
            try:
                date_str = container.find_element(By.CSS_SELECTOR, 'span.bp9Aid').text.strip()
               
            except:
                date_str = ""
            
            if text:
                reviews_data.append({
                    "app_name": app_name, 
                    "review_text": text,
                    "rating": rating,
                    "review_date": date_str, 
                    "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        except Exception as e:
            continue
    return reviews_data

def run_extract(app_name: str, n_reviews: int) -> list[dict]:
    """
    Fungsi utama yang akan dipanggil oleh Airflow Task.
    """
    logging.info(f"Memulai task ekstraksi untuk {app_name}")
    if app_name not in APP_URLS:
        logging.error(f"URL aplikasi {app_name} tidak valid.")
        return []

    driver = None
    results = []
    try:
        driver = init_driver()
        driver.get(APP_URLS[app_name])
        time.sleep(3)
        
        review_elements = scroll_and_load(driver, target_count=n_reviews)
        results = parse_reviews(review_elements, app_name)
        logging.info(f"Berhasil mengekstrak {len(results)} ulasan dari {app_name}.")
        
    except Exception as e:
        logging.error(f"Scraping gagal [{app_name}]: {e}")
        # 👇👇 ALARM KEGAGALAN (Hard Failure) 👇👇
        raise e 
    finally:
        if driver:
            driver.quit()
            logging.info("Browser ditutup.")
            
    return results

# Blok testing manual
if __name__ == "__main__":
    print("Mencoba testing manual...")
    sample_data = run_extract("tokopedia", 10) 
    print(f"Hasil ekstraksi pertama: {sample_data[0] if sample_data else 'Kosong'}")