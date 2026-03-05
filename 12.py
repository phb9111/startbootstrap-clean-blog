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

    post_links_html = ""

    # 🚩 핵심 패치: 모든 링크에 매니저님의 공식 도로명 주소(/startbootstrap-clean-blog/)를 박아 넣습니다.
    BASE_URL = "/startbootstrap-clean-blog"

    nav_bar_html = f'''
    <nav class="navbar navbar-expand-lg navbar-light" id="mainNav">
        <div class="container px-4 px-lg-5">
            <a class="navbar-brand" href="{BASE_URL}/index.html">Hyungbin's LAB</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarResponsive" aria-controls="navbarResponsive" aria-expanded="false" aria-label="Toggle navigation">
                Menu
                <i class="fas fa-bars"></i>
            </button>
            <div class="collapse navbar-collapse" id="navbarResponsive">
                <ul class="navbar-nav ms-auto py-4 py-lg-0">
                    <li class="nav-item"><a class="nav-link px-lg-3 py-3 py-lg-4" href="{BASE_URL}/index.html">Home</a></li>
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
    <link href="https://fonts.googleapis.com/css?family=Open+Sans:300italic,400italic,600italic,700italic,800italic,400,300,600,700,800" rel="stylesheet" type="text/css" />
    <link href="{BASE_URL}/dist/css/styles.css" rel="stylesheet" />
    '''
    
    footer_html = f'''
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="{BASE_URL}/dist/js/scripts.js"></script>
    '''

    for post in posts:
        title_list = post["properties"].get("제목", {}).get("title", [])
        title = title_list[0]["plain_text"] if title_list else "untitled"
        
        date_prop = post["properties"].get("날짜", {}).get("date", {})
        post_date = date_prop["start"][:10] if date_prop and date_prop.get("start") else datetime.now().strftime("%Y-%m-%d")
        
        cat_prop = post["properties"].get("카테고리", {})
        cats = [x["name"] for x in cat_prop.get("multi_select", [])]
        category = cats[0] if cats else "Finance"

        safe_title = title.replace(' ', '-').replace('/', '-')
        file_name = f"{post_date}-{safe_title}.html"
        
        post_links_html += f'''
        <div class="post-preview">
            <a href="{BASE_URL}/{file_name}">
                <h2 class="post-title">{title}</h2>
                <h3 class="post-subtitle">{category}</h3>
            </a>
            <p class="post-meta">작성일: {post_date}</p>
        </div>
        <hr class="my-4" />
        '''

        blocks_url = f"https://api.notion.com/v1/blocks/{post['id']}/children"
        blocks = requests.get(blocks_url, headers=headers).json().get("results", [])
        
        body_html = ""
        for block in blocks:
            if block["type"] == "paragraph":
                text = "".join([t["plain_text"] for t in block["paragraph"].get("rich_text", [])])
                if text.strip():
                    body_html += f"<p>{text}</p>\n"
            elif block["type"] == "image":
                img_data = block["image"]
                img_url = img_data["file"]["url"] if "file" in img_data else img_data["external"]["url"]
                b64_img = get_base64_image(img_url)
                if b64_img:
                    body_html += f'<img src="{b64_img}" style="max-width: 100%; height: auto; border-radius: 5px; margin: 30px 0;">\n'

        post_page = f'''
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <title>{title}</title>
            {head_html}
        </head>
        <body>
            {nav_bar_html}
            <header class="masthead" style="background-image: url('{BASE_URL}/dist/assets/img/post-bg.jpg')">
                <div class="container position-relative px-4 px-lg-5">
                    <div class="row gx-4 gx-lg-5 justify-content-center">
                        <div class="col-md-10 col-lg-8 col-xl-7">
                            <div class="post-heading">
                                <h1>{title}</h1>
                                <span class="meta">작성일: {post_date}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </header>
            <article class="mb-4">
                <div class="container px-4 px-lg-5">
                    <div class="row gx-4 gx-lg-5 justify-content-center">
                        <div class="col-md-10 col-lg-8 col-xl-7">
                            {body_html}
                        </div>
                    </div>
                </div>
            </article>
            {footer_html}
        </body>
        </html>
        '''
        with open(os.path.join(SAVE_PATH, file_name), "w", encoding="utf-8") as f:
            f.write(post_page)

    index_page = f'''
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <title>Hyungbin's LAB</title>
        {head_html}
    </head>
    <body>
        {nav_bar_html}
        <header class="masthead" style="background-image: url('{BASE_URL}/dist/assets/img/home-bg.jpg')">
            <div class="container position-relative px-4 px-lg-5">
                <div class="row gx-4 gx-lg-5 justify-content-center">
                    <div class="col-md-10 col-lg-8 col-xl-7">
                        <div class="site-heading">
                            <h1>Hyungbin's LAB</h1>
                            <span class="subheading">내봄과 꼬미와 나의 성장을 추구합니다.</span>
                        </div>
                    </div>
                </div>
            </div>
        </header>
        <div class="container px-4 px-lg-5">
            <div class="row gx-4 gx-lg-5 justify-content-center">
                <div class="col-md-10 col-lg-8 col-xl-7">
                    {post_links_html}
                </div>
            </div>
        </div>
        {footer_html}
    </body>
    </html>
    '''
    with open(os.path.join(SAVE_PATH, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_page)

if __name__ == "__main__":
    sync_notion_to_blog()
