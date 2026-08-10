"""
OffMall (netmall.hardoff.co.jp) — ハードオフ公式通販 スクレイパー.

ハードオフグループの公式総合中古通販「オフモール」(800店舗以上が出店)。
検索ページはサーバーサイドレンダリングで、商品カード構造:
  <div class="itemcolmn_item">
    <a href="https://netmall.hardoff.co.jp/product/{id}/">
      <div class="item-brand-name">APPLE</div>
      <div class="item-name">iPhone 11</div>
      <div class="item-code">MWLX2J/A</div>
      <div class="item-price"><span class="font-en item-price-en">27,500<span>円</span></span></div>
      <img src="..." alt="iPhone 11|APPLE" />
      ランクバッジ: /assets/images/common/rank/icon-rank-{s|a|b|c}.svg
    </a>
  </div>
ページネーション: ?p={n}&q={keyword}（WordPress標準、next page-numbersリンク）
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://netmall.hardoff.co.jp"
SEARCH_URL = f"{BASE_URL}/search/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# カテゴリURL（オフモールのカテゴリページ）— 空キーワードで全カテゴリスキャンする場合に使用
CATEGORIES = {
    "オーディオ・デジタル家電": "/cate/00010001/",
    "テレビ・モニター": "/cate/00010002/",
    "カメラ": "/cate/00010003/",
    "パソコン・タブレット": "/cate/00010004/",
    "スマートフォン・携帯電話": "/cate/00010005/",
    "ゲーム機": "/cate/00010006/",
    "時計": "/cate/00010007/",
    "楽器": "/cate/00010008/",
    "ブランド品": "/cate/00010009/",
    "ホビー・おもちゃ": "/cate/00010010/",
    "スポーツ・アウトドア": "/cate/00010011/",
    "キッチン・家電": "/cate/00010012/",
    "家具・インテリア": "/cate/00010013/",
}


@dataclass
class SearchResult:
    keyword: str
    page: int
    url: str
    status: int
    total_pages: int = 0
    item_count: int = 0
    items: list[dict] = field(default_factory=list)
    error: Optional[str] = None


async def fetch_page(client: httpx.AsyncClient, url: str, max_retries: int = 3) -> Optional[str]:
    """ページを取得（リトライ付き）"""
    for attempt in range(max_retries):
        try:
            resp = await client.get(url, headers=HEADERS, follow_redirects=True)
            if resp.status_code == 200:
                resp.encoding = "utf-8"
                return resp.text
            # 403/429 はレート制限の可能性 → 待ってリトライ
            if resp.status_code in (403, 429):
                await asyncio.sleep(3 * (attempt + 1))
                continue
            return None
        except httpx.HTTPError:
            await asyncio.sleep(2 * (attempt + 1))
    return None


def parse_item_count(html: str) -> int:
    """全商品数（ページネーションから推定）"""
    # searchInfo またはページ番号から
    pages = re.findall(r'page-numbers[^>]*>(\d+)<', html)
    if pages:
        return int(pages[-1]) * 30
    return 0


def parse_items(html: str) -> list[dict]:
    """商品カードをパース"""
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for card in soup.select("div.itemcolmn_item"):
        a = card.find("a", href=re.compile(r"/product/\d+/"))
        if not a:
            continue
        href = a.get("href", "") or ""
        m = re.search(r"/product/(\d+)/", href)
        if not m:
            continue
        product_id = m.group(1)

        brand_el = card.select_one(".item-brand-name")
        name_el = card.select_one(".item-name")
        code_el = card.select_one(".item-code")
        price_el = card.select_one(".item-price-en")
        img_el = card.select_one("img")
        rank_el = card.select_one("img[src*='icon-rank-']")

        # 価格: "27,500<span>円</span>" 形式
        price = None
        if price_el:
            raw = price_el.get_text(strip=True)
            mm = re.search(r"([\d,]+)", raw)
            if mm:
                price = int(mm.group(1).replace(",", ""))

        rank = ""
        if rank_el:
            src = rank_el.get("src", "") or ""
            rm = re.search(r"icon-rank-([a-z])", src)
            if rm:
                rank = rm.group(1).upper()

        img_url = img_el.get("src", "") if img_el else ""
        title = name_el.get_text(strip=True) if name_el else ""
        if not title:
            continue

        items.append({
            "productId": product_id,
            "title": title,
            "brand": brand_el.get_text(strip=True) if brand_el else "",
            "modelCode": code_el.get_text(strip=True) if code_el else "",
            "price": price,
            "rank": rank,
            "imageUrl": img_url,
            "productUrl": href,
            "shop": "OffMall",
            "source": "offmall",
        })
    return items


async def search_offmall(
    client: httpx.AsyncClient,
    keyword: str = "",
    category: str = "",
    max_pages: int = 2,
    max_items: int = 100,
) -> list[dict]:
    """オフモールを検索（キーワード or カテゴリ）"""
    results: list[dict] = []
    collected = 0

    # 検索URL: キーワード or カテゴリ
    if keyword:
        import urllib.parse
        base = f"{SEARCH_URL}?q={urllib.parse.quote(keyword)}"
    elif category and category in CATEGORIES:
        base = f"{BASE_URL}{CATEGORIES[category]}"
    else:
        base = SEARCH_URL

    page = 1
    while page <= max_pages and collected < max_items:
        url = f"{base}&p={page}" if keyword else f"{base}?p={page}"
        html = await fetch_page(client, url)
        if not html:
            break

        items = parse_items(html)
        if not items:
            break

        for item in items:
            if collected >= max_items:
                break
            item["scrapedAt"] = __import__("datetime").datetime.now().isoformat() + "Z"
            item["category"] = category or "検索:" + keyword
            results.append(item)
            collected += 1

        # 最終ページ判定
        if "next page-numbers" not in html:
            break
        page += 1
        await asyncio.sleep(0.5)

    return results
