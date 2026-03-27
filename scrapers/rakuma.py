"""
ラクマ 検索スクレイパー
Rakuma (Rakuten Flea Market) search scraper
"""
import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote


def search_rakuma(keyword: str, limit: int = 30) -> list[dict]:
    """
    ラクマで商品を検索する
    Returns a list of item dicts: name, price, price_text, image, url, condition, platform
    """
    items = []

    url = f"https://rakuma.rakuten.co.jp/search/?keyword={quote(keyword)}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ja-JP,ja;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"[Rakuma] HTTP {response.status_code}")
            return items

        soup = BeautifulSoup(response.text, "lxml")

        # Try to extract JSON data embedded in the page (Next.js / SSR)
        items = _extract_from_json(soup, limit)

        # Fallback: parse HTML elements
        if not items:
            items = _extract_from_html(soup, limit)

    except requests.RequestException as e:
        print(f"[Rakuma] Request error: {e}")
    except Exception as e:
        print(f"[Rakuma] Unexpected error: {e}")

    return items


def _extract_from_json(soup: BeautifulSoup, limit: int) -> list[dict]:
    """Try to extract items from embedded JSON (Next.js __NEXT_DATA__)"""
    items = []
    script_tag = soup.find("script", id="__NEXT_DATA__")
    if not script_tag or not script_tag.string:
        return items

    try:
        data = json.loads(script_tag.string)
        page_props = data.get("props", {}).get("pageProps", {})

        # Navigate possible data structures
        search_result = (
            page_props.get("items")
            or page_props.get("searchResult", {}).get("items")
            or page_props.get("initialData", {}).get("items")
            or []
        )

        for item in search_result[:limit]:
            try:
                price = int(item.get("price", 0))
                item_id = item.get("itemId") or item.get("id", "")
                image = item.get("image") or item.get("imageUrl") or ""
                if isinstance(image, dict):
                    image = image.get("url", "")
                items.append({
                    "name": item.get("title") or item.get("name", ""),
                    "price": price,
                    "price_text": f"¥{price:,}",
                    "image": image,
                    "url": f"https://rakuma.rakuten.co.jp/item/{item_id}",
                    "condition": item.get("itemStatus") or item.get("condition", ""),
                    "platform": "ラクマ",
                    "platform_key": "rakuma",
                })
            except (ValueError, TypeError):
                continue
    except (json.JSONDecodeError, AttributeError):
        pass

    return items


def _extract_from_html(soup: BeautifulSoup, limit: int) -> list[dict]:
    """Fallback: parse item cards from HTML"""
    items = []

    # Common selectors for item cards
    selectors = [
        "[data-testid='item-card']",
        ".item-box",
        ".search-result-item",
        "li[class*='item']",
        "article[class*='item']",
    ]

    item_elements = []
    for sel in selectors:
        item_elements = soup.select(sel)
        if item_elements:
            break

    for el in item_elements[:limit]:
        try:
            name_el = el.select_one(
                "[class*='name'], [class*='title'], h3, h4, [class*='Name'], [class*='Title']"
            )
            price_el = el.select_one(
                "[class*='price'], [class*='Price']"
            )
            img_el = el.select_one("img")
            link_el = el.select_one("a[href]")

            if not name_el or not price_el:
                continue

            name = name_el.get_text(strip=True)
            price_raw = price_el.get_text(strip=True)
            digits = re.sub(r"[^\d]", "", price_raw)
            if not digits:
                continue
            price = int(digits)

            image = img_el.get("src") or img_el.get("data-src", "") if img_el else ""
            href = link_el.get("href", "") if link_el else ""
            if href and not href.startswith("http"):
                href = "https://rakuma.rakuten.co.jp" + href

            items.append({
                "name": name,
                "price": price,
                "price_text": f"¥{price:,}",
                "image": image,
                "url": href,
                "condition": "",
                "platform": "ラクマ",
                "platform_key": "rakuma",
            })
        except (ValueError, AttributeError):
            continue

    return items
