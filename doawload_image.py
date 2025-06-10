import threading
from queue import Queue
import os
import requests
import json
import time
import random
from fake_useragent import UserAgent
from urllib.parse import urlparse

# ====== Định nghĩa biến ======
JSON_FILE = "dubai_profiles_with_images.json"
SAVE_DIR = "images_user_x"

# ====== Đọc JSON profile ======
with open(JSON_FILE, "r", encoding="utf-8") as f:
    profiles = json.load(f)

# ====== Tạo thư mục lưu ảnh nếu chưa có ======
os.makedirs(SAVE_DIR, exist_ok=True)

# ====== Đưa ảnh vào queue ======
image_queue = Queue()
for profile in profiles:
    profile_id = profile.get("id")
    image_urls = profile.get("images", [])
    for idx, img_url in enumerate(image_urls):
        image_queue.put((profile_id, idx, img_url))

# ====== Hàm tải ảnh đa luồng ======
def download_image_worker():
    session = requests.Session()
    ua = UserAgent()

    while not image_queue.empty():
        try:
            profile_id, idx, img_url = image_queue.get()

            headers = {
                'User-Agent': ua.random,
                'Referer': 'https://vip-dubai-bunnies.com'
            }

            response = session.get(img_url, headers=headers, timeout=10)
            if response.status_code == 200:
                parsed_url = urlparse(img_url)
                filename = os.path.basename(parsed_url.path)  # Lấy phần tên file gốc
                filepath = os.path.join(SAVE_DIR, filename)

                with open(filepath, "wb") as f:
                    f.write(response.content)
                print(f"✅ Đã tải {filename}")
            else:
                print(f"⚠️ Lỗi tải ảnh: {img_url} - Mã {response.status_code}")
        except Exception as e:
            print(f"❌ Lỗi với ảnh {img_url}: {e}")
        finally:
            image_queue.task_done()
            time.sleep(random.uniform(0.5, 1.5))  # chống bị block

# ====== Chạy đa luồng ======
NUM_IMAGE_THREADS = 5  # bạn có thể thay đổi số luồng

threads = []
for _ in range(NUM_IMAGE_THREADS):
    t = threading.Thread(target=download_image_worker)
    t.start()
    threads.append(t)

image_queue.join()
print("✅ Đã tải xong tất cả ảnh.")
