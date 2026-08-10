"""
オフモール（ハードオフ公式通販）スクレイパー エントリポイント。

キーワード検索またはカテゴリ指定で全国800店舗以上が出店する
ハードオフグループ公式総合中古通販サイトから商品データを収集します。
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from apify import Actor
except ImportError:
    Actor = None

from sources.offmall import CATEGORIES, search_offmall


async def run(actor_input: dict) -> list[dict]:
    keyword = str(actor_input.get("searchKeyword", "")).strip()
    category = str(actor_input.get("category", "")).strip()
    max_items = int(actor_input.get("maxItems", 100))
    max_pages = int(actor_input.get("maxPages", 2))

    # プロキシ設定（Apify環境では使用、ローカルでは無視）
    proxy_url = None
    if Actor is not None:
        try:
            proxy_config = await Actor.create_proxy_configuration(
                actor_proxy_input=actor_input.get("proxyConfiguration")
            )
            if proxy_config:
                proxy_url = await proxy_config.new_url()
        except Exception as e:
            print(f"Proxy config skipped: {e}")

    import httpx

    async with httpx.AsyncClient(
        proxy=proxy_url,
        timeout=30.0,
        follow_redirects=True,
    ) as client:
        results = await search_offmall(
            client,
            keyword=keyword,
            category=category,
            max_pages=max_pages,
            max_items=max_items,
        )

    if Actor is not None:
        for item in results:
            await Actor.push_data(item)
        print(f"Collected {len(results)} items from OffMall")
    return results


async def main() -> None:
    if Actor is not None:
        async with Actor:
            actor_input = await Actor.get_input() or {}
            await run(actor_input)
    else:
        # ローカル実行: stdinからJSON入力を受け取る
        raw = sys.stdin.read().strip()
        if raw:
            actor_input = json.loads(raw)
        else:
            actor_input = {}
        results = await run(actor_input)
        for item in results:
            print(json.dumps(item, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
