import requests
import base64
import os
from datetime import datetime

NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
DATABASE_ID = os.environ.get('NOTION_DATABASE_ID')

SAVE_PATH = "./" 
if not os.path.exists(SAVE_PATH):
    os.makedirs(SAVE_PATH)

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# 설정 정보
BLOG_TITLE = "Hyungbin's LAB"
AUTHOR_NAME = "Hyungbin"
BASE_URL = "/startbootstrap-clean-blog"

def get_base64_image(url):
    try:
        image_headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=image_headers, timeout=10)
        if res.status_code == 200:
            content_type = res.headers.get('content-type', 'image/jpeg')
            encoded = base64.b64encode(res.content).decode("utf-8")
            return f"data:{content_type};base64,{encoded}"
    except Exception:
        pass
    return None

def sync_notion_to_blog():
    if not NOTION_TOKEN or not DATABASE_ID:
        return

    # 🚩 전체 데이터 가져오기 (최신순 정렬)
    query_url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    query_data = {
        "filter": {"property": "발행", "checkbox": {"equals": True}},
        "sorts": [{"property": "날짜", "direction": "descending"}]
    }
    res = requests.post(query_url, headers=headers, json=query_data)
    all_posts = res.json().get("results", [])

    # 메뉴바 (Archive 링크 추가)
    nav_bar_html = f'''
    <nav class="navbar navbar-expand-lg navbar-light" id="mainNav">
        <div class="container px-4 px-lg-5">
            <a class="navbar-brand" href="{BASE_URL}/index.html">{BLOG_TITLE}</a>
            <div class="collapse navbar-collapse" id="navbarResponsive">
                <ul class="navbar-nav ms-auto py-4 py-lg-0">
                    <li class="nav-item"><a class="nav-link px-lg-3 py-3 py-lg-4" href="{BASE_URL}/index.html">Home</a></li>
                    <li class="nav-item"><a class="nav-link px-lg-3 py-3 py-lg-4" href="{BASE_URL}/archive.html">Archive</a></li>
                </ul>
            </div>
        </div>
    </nav>
    '''

    head_html = f'''
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
    <script src="https://use.fontawesome.com/releases/v6.3.0/js/all.js" crossorigin="anonymous"></script>
    <link href="https://fonts.googleapis.com/css?family=Lora:400,700,400italic,700italic" rel="stylesheet" type="text/css" />
    <link href="{BASE_URL}/dist/css/styles.css" rel="stylesheet" />
    <style>
        .post-thumbnail {{ width: 120px; height: 80px; object-fit: cover; border-radius: 6px; margin-left: 15px; }}
        .post-item {{ display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #f2f2f2; }}
        .signature {{ border-top: 1px solid #ddd; margin-top: 60px; padding-top: 20px; color: #777; }}
    </style>
    '''
    
    footer_html = f'''
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="{BASE_URL}/dist/js/scripts.js"></script>
    '''

    main_posts_html = "" # 메인 10개용
    archive_posts_html = "" # 전체 리스트용

    for idx, post in enumerate(all_posts):
        title = post["properties"].get("제목", {}).get("title", [{}])[0].get("plain_text", "Untitled")
        date_prop = post["properties"].get("날짜", {}).get("date", {})
        post_date = date_prop["start"][:10] if date_prop and date_prop.get("start") else datetime.now().strftime("%Y-%m-%d")
        category = post["properties"].get("카테고리", {}).get("multi_select", [{}])[0].get("name", "Analysis")

        safe_title = title.replace(' ', '-').replace('/', '-')
        file_name = f"{post_date}-{safe_title}.html"
        
        # 썸네일 및 본문 추출 (최적화를 위해 첫 이미지만 확인)
        blocks_url = f"https://api.notion.com/v1/blocks/{post['id']}/children"
        blocks = requests.get(blocks_url, headers=headers).json().get("results", [])
        
        body_html = ""
        first_image_url = None
        for block in blocks:
            if block["type"] == "paragraph":
                text = "".join([t["plain_text"] for t in block["paragraph"].get("rich_text", [])])
                if text.strip(): body_html += f"<p>{text}</p>\n"
            elif block["type"] == "image":
                img_url = block["image"]["file"]["url"] if "file" in block["image"] else block["image"]["external"]["url"]
                b64_img = get_base64_image(img_url)
                if b64_img:
                    if not first_image_url: first_image_url = b64_img
                    body_html += f'<img src="{b64_img}" style="max-width: 100%; border-radius: 8px; margin: 25px 0;">\n'

        # 공통 아이템 구성
        thumb_tag = f'<img src="{first_image_url}" class="post-thumbnail">' if first_image_url else ''
        post_item_html = f'''
        <div class="post-item">
            <div style="flex: 1;">
                <a href="{BASE_URL}/{file_name}" style="text-decoration: none; color: #333;">
                    <h2 style="font-size: 1.3rem; font-weight: 700; margin-bottom: 5px;">{title}</h2>
                </a>
                <p style="font-size: 0.8rem; color: #888; margin: 0;">{post_date} | {category}</p>
            </div>
            {thumb_tag}
        </div>
        '''

        # 아카이브 리스트에는 무조건 추가
        archive_posts_html += post_item_html
        
        # 메인 리스트에는 상위 10개만 추가
        if idx < 10:
            main_posts_html += post_item_html

        # 개별 포스트 페이지 생성
        post_page = f'''
        <!DOCTYPE html>
        <html lang="ko">
        <head><title>{title} - {BLOG_TITLE}</title>{head_html}</head>
        <body>
            {nav_bar_html}
            <header class="masthead" style="background-image: url('{BASE_URL}/dist/assets/img/post-bg.jpg')">
                <div class="container position-relative px-4 px-lg-5"><div class="row justify-content-center"><div class="col-md-10 col-lg-8">
                    <div class="post-heading"><h1>{title}</h1><span class="meta">Posted by {AUTHOR_NAME} on {post_date}</span></div>
                </div></div></div>
            </header>
            <article class="mb-4"><div class="container px-4 px-lg-5"><div class="row justify-content-center"><div class="col-md-10 col-lg-8">
                {body_html}
                <div class="signature"><p>작성자 : <b>{AUTHOR_NAME}</b></p></div>
                <div class="d-flex justify-content-end mt-5"><a class="btn btn-primary text-uppercase" href="{BASE_URL}/index.html">← 목록으로</a></div>
            </div></div></div></article>
            {footer_html}
        </body>
        </html>
        '''
        with open(os.path.join(SAVE_PATH, file_name), "w", encoding="utf-8") as f:
            f.write(post_page)

    # 🚩 Archive 페이지 생성
    archive_page = f'''
    <!DOCTYPE html>
    <html lang="ko">
    <head><title>Archive - {BLOG_TITLE}</title>{head_html}</head>
    <body>
        {nav_bar_html}
        <header class="masthead" style="background-image: url('{BASE_URL}/dist/assets/img/about-bg.jpg')">
            <div class="container position-relative px-4 px-lg-5"><div class="row justify-content-center"><div class="col-md-10 col-lg-8">
                <div class="site-heading"><h1>Archive</h1><span class="subheading">Archive</span></div>
            </div></div></div>
        </header>
        <div class="container px-4 px-lg-5"><div class="row justify-content-center"><div class="col-md-10 col-lg-8">{archive_posts_html}</div></div></div>
        {footer_html}
    </body>
    </html>
    '''
    with open(os.path.join(SAVE_PATH, "archive.html"), "w", encoding="utf-8") as f:
        f.write(archive_page)

    # 메인 페이지 생성
    index_page = f'''
    <!DOCTYPE html>
    <html lang="ko">
    <head><title>{BLOG_TITLE}</title>{head_html}</head>
    <body>
        {nav_bar_html}
        <header class="masthead" style="background-image: url('{BASE_URL}/dist/assets/img/home-bg.jpg')">
            <div class="container position-relative px-4 px-lg-5"><div class="row justify-content-center"><div class="col-md-10 col-lg-8">
                <div class="site-heading"><h1>{BLOG_TITLE}</h1><span class="subheading">Quantitative Finance & Automation Archive</span></div>
            </div></div></div>
        </header>
        <div class="container px-4 px-lg-5"><div class="row justify-content-center"><div class="col-md-10 col-lg-8">{main_posts_html}</div></div></div>
        {footer_html}
    </body>
    </html>
    '''
    with open(os.path.join(SAVE_PATH, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_page)

if __name__ == "__main__":
    sync_notion_to_blog()
