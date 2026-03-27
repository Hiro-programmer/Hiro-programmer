"""
Yahoo!フリマ 検索スクレイパー
Yahoo! Fleamarket (formerly PayPay Fleamarket) search scraper
"""
import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote


def search_yahoo_flea(keyword: str, limit: int = 30) -> list[dict]:
    """
    Yahoo!フリマで商品を検索する
    Returns a list of item dicts: name, price, price_text, image, url, condition, platform
    """
    items = []

    url = f"https://paypayfleamarket.yahoo.co.jp/search/{quote(keyword)}"
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
            print(f"[Yahoo フリマ] HTTP {response.status_code}")
            return items

        soup = BeautifulSoup(response.text, "lxml")

        # Try embedded JSON first (Next.js)
        items = _extract_from_json(soup, limit)

        # Fallback to HTML parsing
        if not items:
            items = _extract_from_html(soup, limit)

    except requests.RequestException as e:
        print(f"[Yahoo フリマ] Request error: {e}")
    except Exception as e:
        print(f"[Yahoo フリマ] Unexpected error: {e}")

    return items


def _extract_from_json(soup: BeautifulSoup, limit: int) -> list[dict]:
    """Try to extract items from __NEXT_DATA__ or similar embedded JSON"""
    items = []

    # Next.js data
    script_tag = soup.find("script", id="__NEXT_DATA__")
    if script_tag and script_tag.string:
        try:
            data = json.loads(script_tag.string)
            page_props = data.get("props", {}).get("pageProps", {})
            search_items = (
                page_props.get("items")
                or page_props.get("searchItems")
                or page_props.get("initialState", {}).get("items")
                or _deep_find_items(page_props)
                or []
            )
            items = _parse_item_list(search_items, limit)
            if items:
                return items
        except (json.JSONDecodeError, AttributeError):
            pass

    # Inline JSON in other script tags
    for script in soup.find_all("script"):
        content = script.string or ""
        if "itemList" in content or "searchResult" in content:
            match = re.search(r'"items"\s*:\s*(\[.*?\])', content, re.DOTALL)
            if match:
                try:
                    raw = json.loads(match.group(1))
                    items = _parse_item_list(raw, limit)
                    if items:
                        return items
                except json.JSONDecodeError:
                    pass

    return items


def _deep_find_items(obj, depth: int = 0) -> list:
    """Recursively search for an 'items' list inside nested dicts"""
    if depth > 5:
        return []
    if isinstance(obj, dict):
        if "items" in obj and isinstance(obj["items"], list):
            return obj["items"]
        for v in obj.values():
            result = _deep_find_items(v, depth + 1)
            if result:
                return result
    return []


def _parse_item_list(raw_items: list, limit: int) -> list[dict]:
    """Parse a list of raw item dicts into a normalized format"""
    items = []
    for item in raw_items[:limit]:
        if not isinstance(item, dict):
            continue
        try:
            price = int(item.get("price", 0))
            item_id = item.get("itemId") or item.get("id", "")
            image = item.get("image") or item.get("imageUrl") or item.get("thumbnail", "")
            if isinstance(image, dict):
                image = image.get("url", "")
            items.append({
                "name": item.get("title") or item.get("name", ""),
                "price": price,
                "price_text": f"¥{price:,}",
                "image": image,
                "url": f"https://paypayfleamarket.yahoo.co.jp/item/{item_id}",
                "condition": item.get("itemStatus") or item.get("condition", ""),
                "platform": "Yahoo!フリマ",
                "platform_key": "yahoo_flea",
            })
        except (ValueError, TypeError):
            continue
    return items


def _extract_from_html(soup: BeautifulSoup, limit: int) -> list[dict]:
    """Fallback: parse item cards from HTML structure"""
    items = []

    selectors = [
        "[data-testid='item-card']",
        "[class*='ItemCard']",
        "[class*='item-card']",
        "li[class*='item']",
        "article",
    ]

    item_elements = []
    for sel in selectors:
        item_elements = soup.select(sel)
        if item_elements:
            break

    for el in item_elements[:limit]:
        try:
            name_el = el.select_one(
                "[class*='name'], [class*='title'], [class*='Name'], [class*='Title'], h3, h4"
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
                href = "https://paypayfleamarket.yahoo.co.jp" + href

            items.append({
                "name": name,
                "price": price,
                "price_text": f"¥{price:,}",
                "image": image,
                "url": href,
                "condition": "",
                "platform": "Yahoo!フリマ",
                "platform_key": "yahoo_flea",
            })
        except (ValueError, AttributeError):
            continue

    return items
