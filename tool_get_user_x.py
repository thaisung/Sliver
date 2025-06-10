import threading
import requests
from bs4 import BeautifulSoup
import re
import json
from queue import Queue
import time
import random
from fake_useragent import UserAgent

# ========================
BASE_URL = "https://vip-dubai-bunnies.com/all-dubai-escorts-uae-1" + ("/page/{}/" if '{}' in "{}" else "/")
START_PAGE = 1
END_PAGE = 200
NUM_THREADS = 5

# ========================
url_queue = Queue()
unique_phones = {}  # key: phone, value: page number
lock = threading.Lock()

# ========================
def extract_phone_numbers(html):
    soup = BeautifulSoup(html, "html.parser")
    phones = []
    for a in soup.find_all('a', class_='girl-name'):
        text = a.get_text(strip=True)
        matches = re.findall(r'\+\d{8,20}', text)
        phones.extend(matches)
    return phones

def extract_phone_infos(html):
    soup = BeautifulSoup(html, "html.parser")
    phone_infos = []

    girl_divs = soup.find_all("div", class_="girl")
    for girl in girl_divs:
        a_tag = girl.find("a", class_="girl-name")
        if a_tag:
            text = a_tag.get_text(strip=True)
            href = a_tag.get("href")
            matches = re.findall(r'\+\d{8,20}', text)
            for phone in matches:
                phone_infos.append({
                    "phone": phone,
                    "link": href
                })

    return phone_infos


# ========================
def get_page_number_from_url(url):
    match = re.search(r'/page/(\d+)/', url)
    if match:
        return int(match.group(1))
    else:
        print(f"[WARNING] Không tìm thấy số trang trong URL: {url}")
        return 1

# ========================
def worker():
    session = requests.Session()
    ua = UserAgent()
    while not url_queue.empty():
        url = url_queue.get()
        page_num = get_page_number_from_url(url)

        headers = {
            'User-Agent': ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Referer': 'https://google.com'
        }

        try:
            response = session.get(url, headers=headers, timeout=10)
            print(f"url:{url}---code:{response.status_code}")
            if response.status_code == 200:
                phone_infos = extract_phone_infos(response.text)
                with lock:
                    for info in phone_infos:
                        phone = info["phone"]
                        if phone not in unique_phones:
                            unique_phones[phone] = {
                                "page": page_num,
                                "link": info["link"]
                            }
                print(f"[OK] Trang {page_num} - {len(phone_infos)} số")
            else:
                print(f"[LỖI] Trang {page_num} - Status: {response.status_code}")
        except Exception as e:
            print(f"[LỖI] Exception tại {url}: {e}")

        url_queue.task_done()
        print(f'Xong trang : {url}')
        time.sleep(random.uniform(0.5, 2.0))

# ========================
for page in range(START_PAGE, END_PAGE + 1):
    url = BASE_URL.format(page)
    url_queue.put(url)

# ========================
threads = []
for _ in range(NUM_THREADS):
    t = threading.Thread(target=worker)
    t.start()
    threads.append(t)

url_queue.join()

# ========================
# Lưu dữ liệu dạng mảng JSON
output_file = "dubai_phone_numbers_with_links.json"
phone_list = [
    {
        "id": idx + 1,
        "phone": phone,
        "page": info["page"],
        "link": info["link"]
    }
    for idx, (phone, info) in enumerate(sorted(unique_phones.items(), key=lambda x: x[1]["page"]))
] 

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(phone_list, f, indent=4, ensure_ascii=False)

print(f"✅ Đã lưu vào '{output_file}' (mỗi object gồm: số điện thoại, trang, link)")

