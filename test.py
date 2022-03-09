import requests, datetime, re, os
if os.getenv('WHEREAMI') == 'DEV':
  import config
from bs4 import BeautifulSoup
from google.cloud import firestore

def update_blog(request = None):
  if os.getenv("WHEREAMI") == "DEV":
    PROJECT_ID = config.PROJECT_ID
  db = firestore.Client(project=config.PROJECT_ID)
  batch = db.batch()

  blog_list = get_list()

  for blog in blog_list:
    blog_ref = db.collection("blog").document(blog["id"])
    del blog["id"]
    batch.set(blog_ref, blog)

  batch.commit()

# Webページを取得して解析する
def get_list():
  
  base_url = "https://jp.finalfantasyxiv.com"
  load_url = base_url + "/lodestone/blog/?list_type=list&exclusion_key="

  ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6)" \
      "AppleWebKit/537.36 (KHTML, like Gecko)" \
      "Chrome/60.0.3112.113"

  html = requests.get(load_url, headers={"User-Agent": ua})
  soup = BeautifulSoup(html.content, "html.parser")

  blog_list = soup.find(class_="ldst__window").find_all(class_="entry__blog")
  blog_dict_list = []

  for blog in blog_list:
    
    blog_dict = {}

    # タグ
    tags = blog.find(class_="entry__blog__tag")
    if tags is None:
      blog_dict["tags"] = []
    else:
      tag_list = []
      p = r"\[(.*)\]"
      for tag in tags.find_all("li"):
        tag_list.append(re.search(p, tag.text)[1])  # []を含めない
      if "固定" in tag_list or r".*メンバー募集" in tag_list: # TODO: 固定に関する募集以外の日記も出なくなる？
        continue

      blog_dict["tags"] = tag_list
    
    # タイトル
    blog_dict["title"] = blog.find(class_="entry__blog__title").text
    if re.match(r".*(メンバー)|(固定).*(募集)|(探しています).*", blog_dict["title"]):
      continue
    # TODO: そのうち「固定募集or探しています」系は完全に除外したい
    
    # 時間
    blog_dict["time"] = datetime.datetime.fromtimestamp(int(blog.find(class_="datetime_dynamic_ymdhm")["data-epoch"]))
    
    # URL
    blog_dict["url"] = base_url + blog.a["href"]

    # ID(独自)
    id_before = re.search(r'character\/(.+)\/blog', blog_dict["url"]).group(1)
    id_after = re.search(r'blog\/(.+)\/', blog_dict["url"]).group(1)
    blog_dict["id"] = id_before + id_after
    
    # コメント数
    comments = blog.find(class_="entry__blog__header__comment js__tooltip")
    if comments is None:
      blog_dict["comments"] = 0
    else:
      blog_dict["comments"] = int(comments.span.text)

    # いいね数
    likes = blog.find(class_="entry__blog__header__like js__tooltip")
    if likes is None:
      blog_dict["likes"] = 0
    else:
      blog_dict["likes"] = int(likes.span.text)

    # キャラクター名
    blog_dict["character"] = blog.find(class_="entry__blog__search__chara__name").text

    blog_dict_list.append(blog_dict)

  return blog_dict_list