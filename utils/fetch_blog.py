import os
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


BLOG_ROOT = "https://www.zenergytea.com/blogs/matcha-notes-journals"
OUTPUT_DIR = "posts"
TIMEOUT_SECONDS = 20


def clean_text(text):
    """Clean text for YAML frontmatter and Markdown output."""
    if not text:
        return ""
    return (
        text.replace('"', "'")
        .replace("\r", " ")
        .replace("\n", " ")
        .strip()
    )


def slugify(value, fallback="untitled"):
    """Create filesystem- and URL-safe slugs for MkDocs/GitHub Pages."""
    value = value.lower().strip()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return (value or fallback)[:80].strip("-") or fallback


def normalize_date(value):
    """Return a YAML-safe date string.

    Shopify themes often expose human-readable dates. MkDocs does not need a
    strict date type here, so keep invalid/unknown values quoted downstream.
    """
    if not value or value.lower() == "unknown":
        return "Unknown"
    return clean_text(value)


def get_article_links():
    res = requests.get(BLOG_ROOT, timeout=TIMEOUT_SECONDS)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")
    links = soup.select("a[href*='/blogs/matcha-notes-journals/']")
    article_urls = set()

    for a in links:
        href = a.get("href", "")
        if href.startswith("/blogs/matcha-notes-journals/"):
            article_urls.add(urljoin(BLOG_ROOT, href))
        elif href.startswith(BLOG_ROOT + "/"):
            article_urls.add(href)

    return sorted(article_urls)


def extract_article_data(url):
    res = requests.get(url, timeout=TIMEOUT_SECONDS)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    title_tag = soup.find("h1")
    date_tag = soup.find("time")
    author_tag = soup.find("span", string=lambda x: x and "Chang Liu" in x)
    summary_tag = soup.select_one("div.article-template__content p")

    title = clean_text(title_tag.text) if title_tag else "Untitled"
    date = normalize_date(date_tag.text.strip()) if date_tag else "Unknown"
    author = clean_text(author_tag.text) if author_tag else "Chang Liu"
    summary = clean_text(summary_tag.text) if summary_tag else ""

    seo_title_tag = soup.find("title")
    seo_description_tag = soup.find("meta", {"name": "description"})
    seo_keywords_tag = soup.find("meta", {"name": "keywords"})

    seo_title = clean_text(seo_title_tag.text) if seo_title_tag else ""
    seo_description = clean_text(seo_description_tag.get("content", "")) if seo_description_tag else ""
    seo_keywords = clean_text(seo_keywords_tag.get("content", "")) if seo_keywords_tag else ""

    h2_tags = soup.select("div.article-template__content h2")
    h2s = [clean_text(h2.text) for h2 in h2_tags if clean_text(h2.text)]

    # Prefer Shopify article handle as the slug source. It is already URL-safe.
    handle = urlparse(url).path.rstrip("/").split("/")[-1]
    slug = slugify(handle or title)

    return {
        "title": title,
        "date": date,
        "author": author,
        "summary": summary,
        "h2s": h2s,
        "url": url,
        "slug": slug,
        "seo_title": seo_title,
        "seo_description": seo_description,
        "seo_keywords": seo_keywords,
    }


def yaml_quote(value):
    escaped = clean_text(value).replace("\\", "\\\\").replace('"', "'")
    return f'"{escaped}"'


def format_markdown(data):
    frontmatter = "\n".join([
        "---",
        f"title: {yaml_quote(data['title'])}",
        f"date: {yaml_quote(data['date'])}",
        f"author: {yaml_quote(data['author'])}",
        f"source: {yaml_quote(data['url'])}",
        f"seo_title: {yaml_quote(data['seo_title'])}",
        f"seo_description: {yaml_quote(data['seo_description'])}",
        f"seo_keywords: {yaml_quote(data['seo_keywords'])}",
        f"generated_at: {yaml_quote(datetime.utcnow().isoformat(timespec='seconds') + 'Z')}",
        "---",
        "",
    ])

    summary_block = f"> **Summary**:\n> {data['summary']}\n\n" if data["summary"] else ""
    source_block = f"[Read the original article]({data['url']})\n\n"
    h2_block = "\n\n".join([f"## {h}" for h in data["h2s"]])
    return frontmatter + f"# {data['title']}\n\n" + summary_block + source_block + h2_block + "\n"


def save_article(data):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = os.path.join(OUTPUT_DIR, f"{data['slug']}.md")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(format_markdown(data))
    return filename


def main():
    links = get_article_links()
    print(f"Found {len(links)} articles.")

    for url in links:
        try:
            data = extract_article_data(url)
            filename = save_article(data)
            print(f"Saved: {filename}")
        except Exception as e:
            print(f"Error processing {url}: {e}")


if __name__ == "__main__":
    main()
