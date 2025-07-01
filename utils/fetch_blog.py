import requests, os
from bs4 import BeautifulSoup
from datetime import datetime

BLOG_URL = "https://www.zenergytea.com/blogs/matcha-notes-journals"
SAVE_DIR = "posts"

def fetch_blog_links():
    res = requests.get(BLOG_URL)
    soup = BeautifulSoup(res.text, 'html.parser')
    articles = soup.select('a.article__title')
    links = ["https://www.zenergytea.com" + a['href'] for a in articles]
    return links

def fetch_and_save_summary(url):
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    title_tag = soup.select_one('h1.article__title')
    content_tag = soup.select_one('div.article__content')

    if not title_tag or not content_tag:
        return

    title = title_tag.text.strip()
    slug = url.strip('/').split('/')[-1]
    paragraphs = content_tag.find_all('p')
    summary_text = paragraphs[0].get_text(strip=True) if paragraphs else "Summary unavailable."

    md = f"""---
title: {title}
date: {datetime.today().strftime('%Y-%m-%d')}
tags: [matcha, tea, zenergy]
description: Summary from Zenergy Tea Blog
---

# {title}

**Summary:**  
{summary_text}

👉 [Read the full article on Zenergy Tea →]({url})
"""
    os.makedirs(SAVE_DIR, exist_ok=True)
    with open(f"{SAVE_DIR}/{slug}.md", "w", encoding="utf-8") as f:
        f.write(md)

def main():
    links = fetch_blog_links()
    for url in links:
        fetch_and_save_summary(url)

if __name__ == "__main__":
    main()
