"""
フリマ価格比較ツール - Flask バックエンド
Flea Market Price Comparison Tool - Flask Backend
"""
from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import Flask, jsonify, render_template, request

from scrapers.mercari import search_mercari
from scrapers.rakuma import search_rakuma
from scrapers.yahoo_flea import search_yahoo_flea

app = Flask(__name__)

PLATFORMS = [
    ("mercari",    search_mercari,    "メルカリ",      "#ff4757"),
    ("rakuma",     search_rakuma,     "ラクマ",        "#8e44ad"),
    ("yahoo_flea", search_yahoo_flea, "Yahoo!フリマ",  "#e74c3c"),
]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/search")
def api_search():
    keyword = request.args.get("q", "").strip()
    if not keyword:
        return jsonify({"error": "検索キーワードを入力してください"}), 400
    if len(keyword) > 100:
        return jsonify({"error": "キーワードが長すぎます（100文字以内）"}), 400

    results: dict[str, list] = {}
    summary: dict[str, dict] = {}

    # Search all platforms in parallel
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(fn, keyword): (key, name)
            for key, fn, name, _ in PLATFORMS
        }
        for future in as_completed(futures):
            key, name = futures[future]
            try:
                results[key] = future.result()
            except Exception as e:
                print(f"[{name}] Error: {e}")
                results[key] = []

    # Build summary statistics per platform
    for key, _, name, color in PLATFORMS:
        items = results.get(key, [])
        prices = [item["price"] for item in items if item.get("price", 0) > 0]
        if prices:
            summary[key] = {
                "name": name,
                "color": color,
                "count": len(items),
                "min_price": min(prices),
                "max_price": max(prices),
                "avg_price": int(sum(prices) / len(prices)),
                "min_price_text": f"¥{min(prices):,}",
                "max_price_text": f"¥{max(prices):,}",
                "avg_price_text": f"¥{int(sum(prices) / len(prices)):,}",
            }
        else:
            summary[key] = {
                "name": name,
                "color": color,
                "count": 0,
                "error": "結果なし（取得できませんでした）",
            }

    # Combine all items for the all-in-one view
    all_items = []
    for key, _, _, _ in PLATFORMS:
        all_items.extend(results.get(key, []))

    return jsonify({
        "keyword": keyword,
        "results": results,
        "summary": summary,
        "all_items": sorted(all_items, key=lambda x: x.get("price", 0)),
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
