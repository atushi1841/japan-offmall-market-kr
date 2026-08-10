# 일본 오프몰 중고품 마켓 — 하드오프 공식

**하드오프 그룹 공식 종합 중고 통판 오프몰(전국 800+ 매장) 검색. 카메라, 시계, 악기, 명품, 스마트폰, 게임기 등 13 카테고리.**

> 🇯🇵 English/日本語版: [Japan Market](https://apify.com/fruitful_quintessence)

## Input

| Field | Type | Default | Description |
|---|---|---|---|
| `searchKeyword` | string | `iPhone` | 검색 키워드 |
| `maxItems` | integer | 100 | 최대 수집 개수 |
| `maxPages` | integer | 2 | 소스별 최대 페이지 수 |
| `proxyConfiguration` | object | — | Apify proxy |

## Output Sample

```json
{
  "productId": "6426181",
  "title": "iPhone 11",
  "brand": "APPLE",
  "modelCode": "MWLX2J/A",
  "price": 27500,
  "rank": "B",
  "imageUrl": "https://p1-d9ebd2ee.imageflux.jp/c!/w=231,h=182/201328/2026_08_10_18_26_49.jpg",
  "productUrl": "https://netmall.hardoff.co.jp/product/6426181/",
  "shop": "OffMall",
  "source": "offmall",
  "category": "検索:iPhone",
  "scrapedAt": "2026-08-10T10:10:00Z"
}
```

## Use Cases

- 직구/되팔기: 저가 상품 발견 → 마진 확보
- 시세 조사: 특정 모델의 시장 가격 추이 추적
- 재고 모니터링: 매장 재고 변화 감시

## Pricing

이벤트당 과금 — $0.00005/실행 + **$0.002/건**

## Data Source

공개 상품 정보(명칭, 가격, 브랜드, 재고 상태)만 수집합니다.
