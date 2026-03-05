import requests
import base64
import os
from datetime import datetime

NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
DATABASE_ID = os.environ.get('NOTION_DATABASE_ID')

# 🚩 템플릿이 글을 인식하는 '_posts' 폴더로 지정합니다
SAVE_PATH = "_posts" 

if not os.path.exists(SAVE_PATH):
    os.makedirs(SAVE_PATH)

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def get_base64_image(url):
    try:
        res = requests.get(url)
        if res.status_code == 200:
            encoded = base64.b64encode(res.content).decode("utf-8")
            return f"data:image/jpeg;base64,{encoded}"
    except Exception as e:
        print(f"❌ 이미지 변환 오류: {e}")
    return None

def sync_notion_to_blog():
    query_url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    res = requests.post(query_url, headers=headers, json={"filter": {"property": "발행", "checkbox": {"equals": True}}})
    posts = res.json().get("results", [])

    for post in posts:
        # 1. 제목 추출
        title_list = post["properties"].get("제목", {}).get("title", [])
        title = title_list[0]["plain_text"] if title_list else "untitled"
        
        # 2. 날짜 추출 (Jekyll 규칙용)
        date_prop = post["properties"].get("날짜", {}).get("date", {})
        if date_prop:
            post_date = date_prop.get("start", datetime.now().strftime("%Y-%m-%d"))
        else:
            post_date = datetime.now().strftime("%Y-%m-%d")
            
        # 3. 카테고리
        cat_prop = post["properties"].get("카테고리", {})
        category = "Finance"
        if cat_prop.get("type") == "multi_select":
            cats = [x["name"] for x in cat_prop.get("multi_select", [])]
            category = cats[0] if cats else "Finance"

        # 4. 파일명 생성 (예: 2026-03-05-제목.html)
        safe_title = title.replace(' ', '-').replace('/', '-')
        file_name = f"{post_date}-{safe_title}.html"
        
        print(f"📝 '{file_name}' 생성 중...")

        # (본문 및 이미지 처리 로직은 동일)
        blocks_url = f"https://api.notion.com/v1/blocks/{post['id']}/children"
        blocks = requests.get(blocks_url, headers=headers).json().get("results", [])
        
        body_html = ""
        for block in blocks:
            if block["type"] == "paragraph":
                text = "".join([t["plain_text"] for t in block["paragraph"].get("rich_text", [])])
                if text.strip():
                    body_html += f"<p style='text-align: left;'>{text}</p>\n"
            elif block["type"] == "image":
                img_data = block["image"]
                img_url = img_data["file"]["url"] if "file" in img_data else img_data["external"]["url"]
                b64_img = get_base64_image(img_url)
                if b64_img:
                    body_html += f'<div style="text-align: left; margin: 20px 0;"><img src="{b64_img}" style="max-width: 100%; border-radius: 5px;"></div>\n'

        # 5. 저장 (Header 포함)
        with open(os.path.join(SAVE_PATH, file_name), "w", encoding="utf-8") as f:
            f.write(f"---\nlayout: post\ntitle: \"{title}\"\ndate: {post_date}\ncategories: {category}\n---\n\n")
            f.write(f"<div style='text-align: left;'>\n{body_html}\n</div>")

if __name__ == "__main__":
    sync_notion_to_blog()
