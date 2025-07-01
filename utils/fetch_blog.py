import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin

def clean_text(text):
    return text.replace('"', "'").strip()

BLOG_ROOT = "https://www.zenergytea.com/blogs/matcha-notes-journals"
OUTPUT_DIR = "posts"

def get_article_links():
    res = requests.get(BLOG_ROOT)
    soup = BeautifulSoup(res.text, "html.parser")
    links = soup.select("a[href*='/blogs/matcha-notes-journals/']")
    article_urls = set()

    for a in links:
        href = a["href"]
        if href.startswith("/blogs/matcha-notes-journals/"):
            article_urls.add(urljoin(BLOG_ROOT, href))

    return list(article_urls)

def extract_article_data(url):
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")

    title_tag = soup.find("h1")
    date_tag = soup.find("time")
    author_tag = soup.find("span", string=lambda x: x and "Chang Liu" in x)
    summary_tag = soup.select_one("div.article-template__content p")

    title = title_tag.text.strip() if title_tag else "Untitled"
    date = date_tag.text.strip() if date_tag else "Unknown"
    author = author_tag.text.strip() if author_tag else "Chang Liu"
    summary = summary_tag.text.strip() if summary_tag else ""

    # SEO metadata
    seo_title_tag = soup.find("title")
    seo_description_tag = soup.find("meta", {"name": "description"})
    seo_keywords_tag = soup.find("meta", {"name": "keywords"})

    seo_title = clean_text(seo_title_tag.text) if seo_title_tag else ""
    seo_description = clean_text(seo_description_tag["content"]) if seo_description_tag else ""
    seo_keywords = clean_text(seo_keywords_tag["content"]) if seo_keywords_tag else ""

    # h2 sections
    h2_tags = soup.select("div.article-template__content h2")
    h2s = [h2.text.strip() for h2 in h2_tags]

    return {
        "title": title,
        "date": date,
        "author": author,
        "summary": summary,
        "h2s": h2s,
        "url": url,
        "seo_title": seo_title,
        "seo_description": seo_description,
        "seo_keywords": seo_keywords,
    }

def format_markdown(data):
    frontmatter = f"""---
title: "{data['title']}"
date: {data['date']}
author: "{data['author']}"
source: "{data['url']}"
seo_title: "{data['seo_title']}"
seo_description: "{data['seo_description']}"
seo_keywords: "{data['seo_keywords']}"
---
"""
    summary_block = f"> **Summary**:\n> {data['summary']}\n\n" if data['summary'] else ""
    h2_block = "\n".join([f"## {h}" for h in data['h2s']])
    return frontmatter + summary_block + h2_block

def save_article(data):
    safe_title = data["title"].lower().replace(" ", "-").replace("/", "-")[:50]
    filename = os.path.join(OUTPUT_DIR, f"{safe_title}.md")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(format_markdown(data))

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    links = get_article_links()
    print(f"Found {len(links)} articles.")

    for url in links:
        try:
            data = extract_article_data(url)
            save_article(data)
            print(f"Saved: {data['title']}")
        except Exception as e:
            print(f"Error processing {url}: {e}")

if __name__ == "__main__":
    main()
