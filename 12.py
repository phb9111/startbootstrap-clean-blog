import requests
import base64
import os
import glob
from datetime import datetime

NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
DATABASE_ID = os.environ.get('NOTION_DATABASE_ID')

SAVE_PATH = "./" 
headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# 설정 정보
BLOG_TITLE = "Hyungbin's LAB"
AUTHOR_NAME = "Hyungbin"
BASE_URL = "/startbootstrap-clean-blog"
VERSION = datetime.now().strftime("%Y%m%d%H%M%S")

def get_base64_image(url):
    try:
        image_headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=image_headers, timeout=10)
        if res.status_code == 200:
            content_type = res.headers.get('content-type', 'image/jpeg')
            encoded = base64.b64encode(res.content).decode("utf-8")
            return f"data:{content_type};base64,{encoded}"
    except Exception: pass
    return None

def sync_notion_to_blog():
    if not NOTION_TOKEN or not DATABASE_ID: return

    # 기존 포스트 삭제 (중복 방지)
    old_files = glob.glob(os.path.join(SAVE_PATH, "202*-*.html"))
    for f in old_files:
        try: os.remove(f)
        except: pass

    # 노션 데이터 가져오기
    query_url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    query_data = {
        "filter": {"property": "발행", "checkbox": {"equals": True}},
        "sorts": [{"property": "날짜", "direction": "descending"}]
    }
    res = requests.post(query_url, headers=headers, json=query_data)
    all_posts = res.json().get("results", [])

    cache_control = '''
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    '''

    # 🚩 [복구] 모바일용 navbar-toggler 버튼 추가
    nav_bar_html = f'''
    <nav class="navbar navbar-expand-lg navbar-light" id="mainNav">
        <div class="container px-4 px-lg-5">
            <a class="navbar-brand" href="{BASE_URL}/index.html?v={VERSION}">{BLOG_TITLE}</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarResponsive" aria-controls="navbarResponsive" aria-expanded="false" aria-label="Toggle navigation">
                Menu
                <i class="fas fa-bars"></i>
            </button>
            <div class="collapse navbar-collapse" id="navbarResponsive">
                <ul class="navbar-nav ms-auto py-4 py-lg-0">
                    <li class="nav-item"><a class="nav-link px-lg-3 py-3 py-lg-4" href="{BASE_URL}/index.html?v={VERSION}">Home</a></li>
                    <li class="nav-item"><a class="nav-link px-lg-3 py-3 py-lg-4" href="{BASE_URL}/archive.html?v={VERSION}">Archive</a></li>
                </ul>
            </div>
        </div>
    </nav>
    '''

    head_html = f'''
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
    {cache_control}
    <script src="https://use.fontawesome.com/releases/v6.3.0/js/all.js" crossorigin="anonymous"></script>
    <link href="https://fonts.googleapis.com/css?family=Lora:400,700,400italic,700italic" rel="stylesheet" type="text/css" />
    <link href="{BASE_URL}/dist/css/styles.css?v={VERSION}" rel="stylesheet" />
    <style>
        .post-thumbnail {{ width: 120px; height: 80px; object-fit: cover; border-radius: 6px; margin-left: 15px; }}
        .post-item {{ display: flex; justify-content: space-between; align-items: center; padding: 15px 0; border-bottom: 1px solid #f2f2f2; }}
        .signature {{ border-top: 1px solid #ddd; margin-top: 60px; padding-top: 20px; color: #777; font-size: 0.9rem; }}
        /* 모바일에서 버튼이 잘 보이도록 보정 */
        .navbar-toggler {{ padding: 0.5rem; font-size: 0.8rem; }}
    </style>
    '''
    
    footer_html = f'''
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="{BASE_URL}/dist/js/scripts.js?v={VERSION}"></script>
    '''

    main_posts_html = ""
    archive_posts_html = ""

    for idx, post in enumerate(all_posts):
        props = post.get("properties", {})
        title = props.get("제목", {}).get("title", [{}])[0].get("plain_text", "Untitled")
        date_val = props.get("날짜", {}).get("date", {})
        post_date = date_val.get("start", "")[:10] if date_val else datetime.now().strftime("%Y-%m-%d")
        cat_list = props.get("카테고리", {}).get("multi_select", [])
        category = cat_list[0].get("name", "Analysis") if cat_list else "Analysis"

        safe_title = title.replace(' ', '-').replace('/', '-')
        file_name = f"{post_date}-{safe_title}.html"
        
        blocks_url = f"https://api.notion.com/v1/blocks/{post['id']}/children"
        blocks = requests.get(blocks_url, headers=headers).json().get("results", [])
        
        body_html = ""
        first_image_url = None
        for block in blocks:
            if block["type"] == "paragraph":
                text = "".join([t.get("plain_text", "") for t in block["paragraph"].get("rich_text", [])])
                if text.strip(): body_html += f"<p>{text}</p>\n"
            elif block["type"] == "image":
                img_url = block["image"]["file"]["url"] if "file" in block["image"] else block["image"]["external"]["url"]
                b64_img = get_base64_image(img_url)
                if b64_img:
                    if not first_image_url: first_image_url = b64_img
                    body_html += f'<img src="{b64_img}" style="max-width: 100%; border-radius: 8px; margin: 25px 0;">\n'

        post_item_html = f'''
        <div class="post-item">
            <div style="flex: 1;">
                <a href="{BASE_URL}/{file_name}?v={VERSION}" style="text-decoration: none; color: #333;">
                    <h2 style="font-size: 1.3rem; font-weight: 700; margin-bottom: 5px;">{title}</h2>
                </a>
                <p style="font-size: 0.8rem; color: #888;">{post_date} | {category}</p>
            </div>
            {f'<img src="{first_image_url}" class="post-thumbnail">' if first_image_url else ''}
        </div>
        '''
        archive_posts_html += post_item_html
        if idx < 5: main_posts_html += post_item_html

        # 개별 페이지
        with open(os.path.join(SAVE_PATH, file_name), "w", encoding="utf-8") as f:
            f.write(f'''
            <!DOCTYPE html>
            <html lang="ko">
            <head><title>{title} - {BLOG_TITLE}</title>{head_html}</head>
            <body>
                {nav_bar_html}
                <header class="masthead" style="background-image: url('{BASE_URL}/dist/assets/img/post-bg.jpg')">
                    <div class="container position-relative px-4 px-lg-5"><div class="row justify-content-center">
                        <div class="col-md-10 col-lg-8"><div class="post-heading"><h1>{title}</h1><span class="meta">Posted by {AUTHOR_NAME} on {post_date}</span></div></div>
                    </div></div>
                </header>
                <article class="mb-4"><div class="container px-4 px-lg-5"><div class="row justify-content-center"><div class="col-md-10 col-lg-8">
                    {body_html}
                    <div class="signature"><p>작성자 : <b>{AUTHOR_NAME}</b></p></div>
                    <div class="d-flex justify-content-end mt-5"><a class="btn btn-primary text-uppercase" href="{BASE_URL}/index.html?v={VERSION}">← 목록으로</a></div>
                </div></div></div></article>
                {footer_html}
            </body>
            </html>
            ''')

    # 아카이브 페이지
    with open(os.path.join(SAVE_PATH, "archive.html"), "w", encoding="utf-8") as f:
        f.write(f'''
        <!DOCTYPE html>
        <html lang="ko">
        <head><title>Archive - {BLOG_TITLE}</title>{head_html}</head>
        <body>
            {nav_bar_html}
            <header class="masthead" style="background-image: url('{BASE_URL}/dist/assets/img/about-bg.jpg')">
                <div class="container position-relative px-4 px-lg-5"><div class="row justify-content-center">
                    <div class="col-md-10 col-lg-8"><div class="site-heading"><h1>Archive</h1><span class="subheading">LAB Records</span></div></div>
                </div></div>
            </header>
            <div class="container px-4 px-lg-5"><div class="row justify-content-center"><div class="col-md-10 col-lg-8">{archive_posts_html}</div></div></div>
            {footer_html}
        </body>
        </html>
        ''')

    # 메인 페이지
    with open(os.path.join(SAVE_PATH, "index.html"), "w", encoding="utf-8") as f:
        f.write(f'''
        <!DOCTYPE html>
        <html lang="ko">
        <head><title>{BLOG_TITLE}</title>{head_html}</head>
        <body>
            {nav_bar_html}
            <header class="masthead" style="background-image: url('{BASE_URL}/dist/assets/img/home-bg.jpg')">
                <div class="container position-relative px-4 px-lg-5"><div class="row justify-content-center">
                    <div class="col-md-10 col-lg-8"><div class="site-heading"><h1>{BLOG_TITLE}</h1><span class="subheading">Quantitative Finance Archive</span></div></div>
                </div></div>
            </header>
            <div class="container px-4 px-lg-5"><div class="row justify-content-center">
                <div class="col-md-10 col-lg-8">
                    {main_posts_html}
                    <div class="d-flex justify-content-end mb-4" style="margin-top: 30px;">
                        <a class="btn btn-primary text-uppercase" href="{BASE_URL}/archive.html?v={VERSION}">Older Posts →</a>
                    </div>
                </div>
            </div></div>
            {footer_html}
        </body>
        </html>
        ''')

if __name__ == "__main__":
    sync_notion_to_blog()
