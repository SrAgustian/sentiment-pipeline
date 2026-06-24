import os
os.environ['WDM_SSL_VERIFY'] = '0'
import time
import random
import csv
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from webdriver_manager.chrome import ChromeDriverManager

def init_driver(headless=False):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def scroll_and_load(driver, target_count=1000):
    print("Mencari tombol 'Lihat semua ulasan'...")
    try:
        see_all_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Lihat semua') or contains(text(),'See all')]"))
        )
        see_all_btn.click()
        print("Tombol berhasil diklik! Kotak ulasan terbuka.")
        time.sleep(3)
    except Exception as e:
        print("Tombol tidak ditemukan atau sudah terbuka.")
    
    print(f"\nMulai scrolling untuk mencapai target {target_count} ulasan...")
    prev_count = 0
    stall_limit = 5 
    stall = 0
    
    while True:
        reviews = driver.find_elements(By.CSS_SELECTOR, 'div[class*="RHo1pe"]')
        current_count = len(reviews)
        print(f"  Ter-load: {current_count} ulasan")
        
        if current_count >= target_count:
            print(f"Target {target_count} tercapai!")
            break
        
        if current_count == prev_count:
            stall += 1
            if stall >= stall_limit:
                print("Mentok! Tidak ada ulasan baru yang ter-load. Berhenti scroll.")
                break
        else:
            stall = 0
        
        prev_count = current_count
        
        # Native Wheel Scroll)
        if len(reviews) > 0:
            last_review = reviews[-1]
            try:
                # Geser kursor mouse (virtual) ke ulasan terakhir
                ActionChains(driver).move_to_element(last_review).perform()
                time.sleep(0.5)
                
                # Putar roda mouse ke bawah sejauh 5000 pixel
                scroll_origin = ScrollOrigin.from_element(last_review)
                ActionChains(driver).scroll_from_origin(scroll_origin, 0, 5000).perform()
            except Exception as e:
                # Fallback jika ActionChains gagal
                driver.execute_script("arguments[0].scrollIntoView(true);", last_review)
            
        # Jeda 
        time.sleep(random.uniform(3, 5))
        
    return driver.find_elements(By.CSS_SELECTOR, 'div[class*="RHo1pe"]')

def extract_reviews(review_elements, app_name):
    reviews_data = []
    print("\nMulai mengekstrak data ulasan...")
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
                date = container.find_element(By.CSS_SELECTOR, 'span.bp9Aid').text.strip()
            except:
                date = ""
            
            if text:
                reviews_data.append({
                    "app": app_name,
                    "text": text,
                    "rating": rating,
                    "date": date,
                    "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        except Exception as e:
            continue
    return reviews_data

def save_to_csv(data, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["app", "text", "rating", "date", "scraped_at"])
        writer.writeheader()
        writer.writerows(data)
    print(f"BERHASIL! Tersimpan: {len(data)} ulasan -> {filename}")

# --- Eksekusi Program ---
APP_URLS = {
    "shopee"    : "https://play.google.com/store/apps/details?id=com.shopee.id&hl=id",
    "tokopedia" : "https://play.google.com/store/apps/details?id=com.tokopedia.tkpd&hl=id",
    "blibli"    : "https://play.google.com/store/apps/details?id=blibli.mobile.commerce&hl=id"
}

print("Sedang menyiapkan browser...")
driver = init_driver(headless=False)

try:
   
    app_name = "blibli"  # Ganti dengan "shopee" atau "blibli" sesuai kebutuhan
    
    print(f"Membuka halaman {APP_URLS[app_name]}...")
    driver.get(APP_URLS[app_name])
    time.sleep(3) 
    
    
    reviews_elements = scroll_and_load(driver, target_count=10000)
    print(f"\nTotal elemen ulasan yang siap diekstrak: {len(reviews_elements)}")
    
    data = extract_reviews(reviews_elements, app_name)
    if data:
       
        save_to_csv(data, f"data/raw_{app_name}.csv")
    else:
        print("Peringatan: Tidak ada data ulasan yang berhasil diekstrak.")
finally:
    driver.quit()
    print("Selesai dan browser ditutup.")