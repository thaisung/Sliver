import threading
import requests
from bs4 import BeautifulSoup
import re
from openpyxl import Workbook
from queue import Queue
import urllib.request
from urllib.error import URLError, HTTPError
import http.client
from urllib.parse import urlparse
import time
import random

from fake_useragent import UserAgent


# ========================
BASE_URL = "https://vip-dubai-bunnies.com/all-dubai-escorts-uae-1" + ("/page/{}/" if '{}' in "{}" else "/")
START_PAGE = 1
END_PAGE = 400
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

        response = session.get(url, headers=headers, timeout=10)
        print(f"url:{url}---code:{response.status_code}")
        if response.status_code == 200:
            phones = extract_phone_numbers(response.text)
            with lock:
                for phone in phones:
                    if phone not in unique_phones:
                        unique_phones[phone] = page_num
            print(f"[OK] Trang {page_num} - {len(phones)} số")
        else:
            print(f"[LỖI] Trang {page_num} - Status: {response.status_code}")

        url_queue.task_done()

        print(f'Xong trang : {url}')

        # ✅ Thêm delay ngẫu nhiên giữa các lần gọi (0.5 ~ 2.0 giây)
        time.sleep(random.uniform(0.5, 2.0))

# def worker():
#     while not url_queue.empty():
#         url = url_queue.get()
#         page_num = get_page_number_from_url(url)
#         try:
#             parsed_url = urlparse(url)
#             conn = http.client.HTTPSConnection(parsed_url.netloc)

#             headers = {
#                 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36'
#             }

#             conn.request("GET", parsed_url.path, headers=headers)
#             res = conn.getresponse()
#             html = res.read().decode("utf-8")

#             if res.status == 200:
#                 print('text:', html[:1000])  # In ngắn gọn thôi
#                 phones = extract_phone_numbers(html)
#                 print('phones:', phones)
#                 with lock:
#                     for phone in phones:
#                         if phone not in unique_phones:
#                             unique_phones[phone] = page_num
#                 print(f"[OK] Trang {page_num} - {len(phones)} số")
#             else:
#                 print(f"[LỖI] Trang {page_num} - Status: {res.status}")
#         except Exception as e:
#             print(f"[LỖI] Trang {page_num} - {e}")
#         finally:
#             url_queue.task_done()
#         print(f'Xong trang : {url}')

# def worker():
#     while not url_queue.empty():
#         url = url_queue.get()
#         page_num = get_page_number_from_url(url)
#         try:
#             headers = {
#                 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36'
#             }
#             print('Đã call :',url)
#             req = urllib.request.Request(url, headers=headers)
#             with urllib.request.urlopen(req, timeout=15) as response:
#                 html = response.read().decode("utf-8")
#                 print('text:', html[:1000])  # chỉ in 1000 ký tự đầu để đỡ dài
#                 phones = extract_phone_numbers(html)
#                 print('phones:', phones)
#                 with lock:
#                     for phone in phones:
#                         if phone not in unique_phones:
#                             unique_phones[phone] = page_num
#                 print(f"[OK] Trang {page_num} - {len(phones)} số")
#         except HTTPError as e:
#             print(f"[LỖI] Trang {page_num} - HTTP Error: {e.code}")
#         except URLError as e:
#             print(f"[LỖI] Trang {page_num} - URL Error: {e.reason}")
#         except Exception as e:
#             print(f"[LỖI] Trang {page_num} - {e}")
#         finally:
#             url_queue.task_done()
#         print(f'Xong trang : {url}')

# ========================
for page in range(START_PAGE, END_PAGE + 1):
    url = BASE_URL.format(page)
    url_queue.put(url)

# print('url_queue:',url_queue)

# ========================
threads = []
for _ in range(NUM_THREADS):
    t = threading.Thread(target=worker)
    t.start()
    threads.append(t)

url_queue.join()

# ========================
wb = Workbook()
ws = wb.active
ws.title = "Phone Numbers"
ws.append(["Phone Number", "Found On Page"])

for phone, page_num in sorted(unique_phones.items(), key=lambda x: x[1]):
    ws.append([phone, page_num])


wb.save("dubai_phone_numbers_by_page_1_400.xlsx")
print("✅ Đã lưu vào 'dubai_phone_numbers_by_page_1_400.xlsx' (không trùng, có số trang)")
