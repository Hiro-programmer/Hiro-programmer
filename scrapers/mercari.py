"""
メルカリ 検索スクレイパー
Mercari Japan search scraper
"""
import requests
import json
from urllib.parse import quote


def search_mercari(keyword: str, limit: int = 30) -> list[dict]:
    """
    メルカリで商品を検索する
    Returns a list of item dicts: name, price, price_text, image, url, condition, platform
    """
    items = []

    # Mercari internal search API
    url = "https://api.mercari.jp/v2/entities:search"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json",
        "Accept-Language": "ja-JP,ja;q=0.9,en;q=0.8",
        "X-Platform": "web",
        "Origin": "https://jp.mercari.com",
        "Referer": "https://jp.mercari.com/",
        "DPOP": "dummy",
    }
    payload = {
        "keyword": keyword,
        "limit": limit,
        "sort": "SORT_SCORE",
        "order": "ORDER_DESC",
        "status": ["STATUS_TRADING"],
        "itemTypes": [],
        "skus": [],
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            data = response.json()
            for item in data.get("items", []):
                try:
                    price = int(item.get("price", 0))
                    thumbnails = item.get("thumbnails", [])
                    image = thumbnails[0] if thumbnails else ""
                    condition_obj = item.get("itemCondition") or {}
                    items.append({
                        "name": item.get("name", ""),
                        "price": price,
                        "price_text": f"¥{price:,}",
                        "image": image,
                        "url": f"https://jp.mercari.com/item/{item.get('id', '')}",
                        "condition": condition_obj.get("name", ""),
                        "platform": "メルカリ",
                        "platform_key": "mercari",
                    })
                except (ValueError, TypeError):
                    continue
    except requests.RequestException as e:
        print(f"[Mercari] Request error: {e}")
    except Exception as e:
        print(f"[Mercari] Unexpected error: {e}")

    return items
