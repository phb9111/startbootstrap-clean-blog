import requests
import base64
import os
from datetime import datetime

NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
DATABASE_ID = os.environ.get('NOTION_DATABASE_ID')

# 🚩 핵심: 저장 위치를 매니저님의 진짜 메인 주소인 'dist' 폴더로 지정합니다!
SAVE_PATH = "dist" 
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
    if not NOTION_TOKEN or not DATABASE_ID:
        print("❌ 에러: 토큰이 설정되지 않았습니다.")
        return

    query_url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    res = requests.post(query_url, headers=headers, json={"filter": {"property": "발행", "checkbox": {"equals": True}}})
    posts = res.json().get("results", [])

    post_links_html = "" # 메인 화면(index.html)에 띄울 글 목록

    for post in posts:
        # 제목 및 날짜 추출
        title_list = post["properties"].get("제목", {}).get("title", [])
        title = title_list[0]["plain_text"] if title_list else "untitled"
        
        date_prop = post["properties"].get("날짜", {}).get("date", {})
        post_date = date_prop["start"][:10] if date_prop and date_prop.get("start") else datetime.now().strftime("%Y-%m-%d")
        
        cat_prop = post["properties"].get("카테고리", {})
        cats = [x["name"] for x in cat_prop.get("multi_select", [])]
        category = cats[0] if cats else "Finance"

        safe_title = title.replace(' ', '-').replace('/', '-')
        file_name = f"{post_date}-{safe_title}.html" # 🚩 다시 html 파일로 만듭니다
        
        # 1. 메인 화면에 들어갈 '글 목록' 블록 조립
        post_links_html += f'''
        <div class="post-preview" style="margin-bottom: 30px; padding-bottom: 30px; border-bottom: 1px solid #eee;">
            <a href="{file_name}" style="text-decoration: none; color: black;">
                <h2 class="post-title" style="margin-bottom: 5px;">{title}</h2>
                <h4 class="post-subtitle" style="font-weight: normal; color: gray; margin-top: 0;">{category}</h4>
            </a>
            <p class="post-meta" style="color: gray; font-size: 0.9em;">작성일: {post_date}</p>
        </div>
        '''

        # 본문 내용 추출
        blocks_url = f"https://api.notion.com/v1/blocks/{post['id']}/children"
        blocks = requests.get(blocks_url, headers=headers).json().get("results", [])
        
        body_html = ""
        for block in blocks:
            if block["type"] == "paragraph":
                text = "".join([t["plain_text"] for t in block["paragraph"].get("rich_text", [])])
                if text.strip():
                    body_html += f"<p style='line-height: 1.8; text-align: left;'>{text}</p>\n"
            elif block["type"] == "image":
                img_data = block["image"]
                img_url = img_data["file"]["url"] if "file" in img_data else img_data["external"]["url"]
                b64_img = get_base64_image(img_url)
                if b64_img:
                    body_html += f'<div style="text-align: center; margin: 30px 0;"><img src="{b64_img}" style="max-width: 100%; border-radius: 5px;"></div>\n'

        # 2. 개별 글 페이지(HTML) 생성 및 저장
        post_page = f'''
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="utf-8" />
            <title>{title}</title>
            <link href="css/styles.css" rel="stylesheet" />
        </head>
        <body>
            <header class="masthead" style="background-image: url('assets/img/post-bg.jpg'); padding: 80px 0; text-align: center; background-color: #0085A1; color: white;">
                <h1 style="color: white; font-size: 2.5em; font-weight: bold; margin-bottom: 10px;">{title}</h1>
                <span style="font-size: 1.2em;">{post_date}</span>
            </header>
            <div class="container" style="max-width: 800px; margin: 50px auto; padding: 0 20px;">
                {body_html}
                <div style="margin-top: 50px; text-align: center;">
                    <a href="index.html" style="padding: 10px 20px; background-color: #0085A1; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">← 메인으로 돌아가기</a>
                </div>
            </div>
        </body>
        </html>
        '''
        with open(os.path.join(SAVE_PATH, file_name), "w", encoding="utf-8") as f:
            f.write(post_page)

    # 3. 진짜 메인 화면(dist/index.html)을 덮어쓰기
    index_page = f'''
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="utf-8" />
        <title>박형빈 매니저님의 블로그</title>
        <link href="css/styles.css" rel="stylesheet" />
    </head>
    <body>
        <header class="masthead" style="background-image: url('assets/img/home-bg.jpg'); padding: 100px 0; text-align: center; background-color: #0085A1; color: white;">
            <h1 style="color: white; font-size: 3em; font-weight: bold; margin-bottom: 10px;">자동화 퀀트 블로그</h1>
            <span style="font-size: 1.2em;">노션에 작성하면 15분마다 자동으로 발행됩니다</span>
        </header>
        <div class="container" style="max-width: 800px; margin: 50px auto; padding: 0 20px;">
            {post_links_html}
        </div>
    </body>
    </html>
    '''
    with open(os.path.join(SAVE_PATH, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_page)

if __name__ == "__main__":
    sync_notion_to_blog()
