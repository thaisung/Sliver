import threading
import requests
from bs4 import BeautifulSoup
import json
import time
import random
from queue import Queue
from fake_useragent import UserAgent

# ====== Cấu hình ======
INPUT_FILE = "dubai_phone_numbers_with_links.json"
OUTPUT_FILE = "dubai_profiles_with_images.json"
MAX_ID = 300
NUM_THREADS = 8 # 👈 Số luồng, bạn có thể thay đổi

ua = UserAgent()
profile_queue = Queue()
results = []
lock = threading.Lock()

# ====== Đọc dữ liệu ban đầu ======
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

for item in data:
    if item["id"] <= MAX_ID:
        profile_queue.put(item)


# ====== Hàm xử lý từng profile ======
def get_profile_data(url):
    headers = {
        'User-Agent': ua.random,
        'Accept': 'text/html',
        'Referer': 'https://google.com'
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            print(f"[LỖI] Không lấy được URL: {url} - Mã: {res.status_code}")
            return None

        soup = BeautifulSoup(res.text, "html.parser")

        # Tiêu đề
        h3 = soup.find("h3", class_="profile-title")
        title = h3.get("title") if h3 else ""

        # Trích xuất ảnh
        image_div = soup.find("div", class_="thumbs")
        image_links = []
        if image_div:
            for a in image_div.find_all("a", href=True):
                image_links.append(a["href"])

        # Lấy mô tả thẻ <b> và toàn bộ đoạn giới thiệu
        about_div = soup.find("div", class_="aboutme")
        desc_tag = ""
        about_me = ""

        if about_div:
            b_tag = about_div.find("b")
            if b_tag:
                desc_tag = b_tag.get_text(" ", strip=True)
            about_me = about_div.get_text(separator=" ", strip=True)

        # Trích xuất thông tin chi tiết (cặp <b> và <span>) trong girlinfo
        girlinfo_div = soup.find("div", class_="girlinfo")
        attribute_list = []

        if girlinfo_div:
            for elem in girlinfo_div.children:
                if elem.name == "h4":
                    break  # Dừng lại khi gặp thẻ <h4>
                if elem.name == "b":
                    label = elem.get_text(strip=True).rstrip(':')
                    next_sibling = elem.find_next_sibling("span")
                    if next_sibling and next_sibling.name == "span":
                        value = next_sibling.get_text(strip=True)
                        attribute_list.append({
                            "label": label,
                            "value": value
                        })

        # Trích xuất danh sách dịch vụ
        services_div = soup.find("div", class_="services")
        services = []

        if services_div:
            for div in services_div.find_all("div", recursive=False):
                text = div.get_text(strip=True)
                if text:
                    services.append(text)

        # Tìm div chứa thông tin rates
        girlinfo_r = soup.find("div", class_="girlinfo r")
        rates = {}

        if girlinfo_r:
            # Tìm vị trí thẻ h4 có text "Rates:"
            h4_rates = girlinfo_r.find("h4", string=lambda s: s and "Rates:" in s)
            if h4_rates:
                # Lấy các thẻ <b> và <span> liền kề nhau nằm sau thẻ h4_rates
                sibling = h4_rates.find_next_sibling()
                while sibling:
                    # Nếu gặp thẻ <b> và tiếp theo là <span> thì lấy cặp này
                    if sibling.name == "b":
                        next_span = sibling.find_next_sibling("span")
                        if next_span:
                            key = sibling.get_text(strip=True).rstrip(":")
                            value = next_span.get_text(strip=True)
                            rates[key] = value
                            # Bỏ qua span đã lấy để tránh lặp
                            sibling = next_span.find_next_sibling()
                            continue
                    # Nếu đến thẻ h4 khác hoặc hết phần rates thì dừng
                    if sibling.name == "h4":
                        break
                    sibling = sibling.find_next_sibling()


        return {
            "title": title,
            "images": image_links,
            "desc_tag": desc_tag,
            "about_me": about_me,
            "attributes": attribute_list,
            "services": services,
            "rates": rates
        }


    except Exception as e:
        print(f"[LỖI] Exception với URL {url}: {e}")
        return None


# ====== Worker cho mỗi luồng ======
def worker():
    while not profile_queue.empty():
        item = profile_queue.get()
        print(f"🔍 [Thread {threading.current_thread().name}] Đang xử lý ID {item['id']}")

        profile_data = get_profile_data(item["link"])

        if profile_data:
            result = {
                "id": item["id"],
                "phone": item["phone"],
                "page": item["page"],
                "link": item["link"],
                "title": profile_data["title"],
                "images": profile_data["images"],
                "desc_tag": profile_data["desc_tag"],
                "about_me": profile_data["about_me"],
                "attributes": profile_data["attributes"],
                "services": profile_data["services"],
                "rates": profile_data["rates"]
            }

            with lock:
                results.append(result)

        time.sleep(random.uniform(0.5, 1.5))
        profile_queue.task_done()


# ====== Tạo và chạy các luồng ======
threads = []
for _ in range(NUM_THREADS):
    t = threading.Thread(target=worker)
    t.start()
    threads.append(t)

profile_queue.join()

# ====== Ghi ra file ======
results = sorted(results, key=lambda x: x["id"])  # Sắp xếp theo ID
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

print(f"✅ Đã lưu {len(results)} mục vào '{OUTPUT_FILE}'")
