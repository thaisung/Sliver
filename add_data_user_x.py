import os
import json
import requests
from urllib.parse import urlparse
import uuid
import re

# ====== Cấu hình ======
JSON_FILE = "dubai_profiles_with_images.json"
SAVE_DIR = "images_user_x"

# ====== Tạo thư mục nếu chưa có ======
os.makedirs(SAVE_DIR, exist_ok=True)

# ====== Đọc file JSON ======
with open(JSON_FILE, "r", encoding="utf-8") as f:
    profiles = json.load(f)

# ====== Tải ảnh ======
for profile in profiles:
    text = profile['title']
    match = re.search(r"(\+?\d{7,})$", text)
    phone = match.group(1)
    name = text[:match.start()].strip()
    
    obj = XY.object.create(
        uuid = uuid.uuid4(),
        Avatar = os.path.basename(profile['images'][0]),
        Name = name,
        Phone = phone,
        Overnight ='',
        Year_of_birth='',
        Height = '',
        Weight = '',
        Rounds = '',
        Service = "\n".join(profile['services']),
        Segment = '',
        Content = f"{profile['desc_tag']}\n{profile['about_me']}",
        Price_call_in ='',
        Price_call_out = '',
        Order = '',
        Belong_User='',
        Belong_Region='',
        Belong_Nation='',
    )

    for i in profile['images'][1:]:
        Photo.object.create(
            Avatar=os.path.basename(i),
            Belong_XY='',
            )
