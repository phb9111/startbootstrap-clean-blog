import requests
import base64
import os

# 🚩 깃허브 금고(Secrets)에서 정보를 가져옵니다
NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
DATABASE_ID = os.environ.get('NOTION_DATABASE_ID')
# 🚩 중요: 깃허브 블로그 폴더 내 'posts' 폴더 경로를 적으세요 (예: "./posts")
SAVE_PATH = "./"
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
        print(f"❌ 이미지 오류: {e}")
    return None


def sync_notion_to_blog():
    print("🚀 결산을 다시 시작합니다 (카테고리 및 정렬 수정 버전)...")

    query_url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    res = requests.post(query_url, headers=headers, json={"filter": {"property": "발행", "checkbox": {"equals": True}}})
    posts = res.json().get("results", [])

    for post in posts:
        title = post["properties"]["제목"]["title"][0]["plain_text"]

        # 🚩 카테고리 로직 수정: 다중 선택(multi_select) 대응
        cat_prop = post["properties"].get("카테고리", {})
        category = "미분류"
        if cat_prop.get("type") == "multi_select":
            categories = [x["name"] for x in cat_prop.get("multi_select", [])]
            category = ", ".join(categories) if categories else "미분류"

        print(f"📝 '{title}' ({category}) 처리 중...")

        # 본문 블록 가져오기
        blocks_url = f"https://api.notion.com/v1/blocks/{post['id']}/children"
        blocks = requests.get(blocks_url, headers=headers).json().get("results", [])

        body_html = ""
        for block in blocks:
            if block["type"] == "paragraph":
                text = "".join([t["plain_text"] for t in block["paragraph"].get("rich_text", [])])
                if text.strip():
                    body_html += f"<p style='line-height: 1.8; text-align: left; margin: 10px 0;'>{text}</p>\n"

            elif block["type"] == "image":
                img_data = block["image"]
                img_url = img_data["file"]["url"] if "file" in img_data else img_data["external"]["url"]
                b64_img = get_base64_image(img_url)
                if b64_img:
                    # 🚩 이미지도 군더더기 없이 왼쪽 정렬
                    body_html += f'''
                    <div style="text-align: left; margin: 20px 0;">
                        <img src="{b64_img}" style="max-width: 100%; height: auto; border-radius: 5px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    </div>
                    '''

        # 파일 저장
        file_name = f"{title.replace(' ', '_')}.html"
        with open(os.path.join(SAVE_PATH, file_name), "w", encoding="utf-8") as f:
            # 깃허브가 읽을 헤더
            f.write("---\n")
            f.write(f"layout: post\n")
            f.write(f"title: \"{title}\"\n")
            f.write(f"category: \"{category}\"\n")
            f.write("---\n\n")
            # 🚩 여백 없이 왼쪽 끝부터 시작하는 컨테이너
            f.write(f"<div style='text-align: left; padding: 10px;'>\n")
            f.write(body_html)
            f.write(f"\n</div>")

    print(f"\n✅ 완료! 이제 '{category}'가 정상적으로 찍힐 겁니다.")


if __name__ == "__main__":
    sync_notion_to_blog()