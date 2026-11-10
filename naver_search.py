
import re
import statistics
import requests
import streamlit as st


def clean_text(text):
    return re.sub(r"<[^>]+>", "", text or "")


def extract_prices(text):
    text = clean_text(text)

    prices = []

    # 120,000원 / 120000원
    for match in re.finditer(
        r"(?<![\d.,])(\d{1,3}(?:,\d{3})+|\d{4,8})\s*원",
        text
    ):
        prices.append(int(match.group(1).replace(",", "")))

    # 12만원 / 12.5만원
    for match in re.finditer(
        r"(?<![\d.])(\d+(?:\.\d+)?)\s*만원",
        text
    ):
        prices.append(round(float(match.group(1)) * 10000))

    return list(set(prices))


def normalize(text):
    text = clean_text(text).lower()
    text = text.replace("기가바이트", "gb")
    text = text.replace("기가", "gb")
    return re.sub(r"[^a-z0-9가-힣]", "", text)


def search_cafe(product_name):
    url = "https://naverapihub.apigw.ntruss.com/search/v1/cafearticle"

    headers = {
        "X-NCP-APIGW-API-KEY-ID": st.secrets["NAVER_CLIENT_ID"],
        "X-NCP-APIGW-API-KEY": st.secrets["NAVER_CLIENT_SECRET"]
    }

    params = {
        "query": product_name + " 판매",
        "display": 100,
        "sort": "date"
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=10
    )
    response.raise_for_status()

    return response.json().get("items", [])


def get_market_prices(product_name):
    items = search_cafe(product_name)

    valid_prices = []
    matched_posts = []

    excluded_words = [
        "케이스", "커버", "키링", "스트랩",
        "이어팁", "삽니다", "구매합니다",
        "매입", "교환", "대여", "광고"
    ]

    normalized_product = normalize(product_name)
    product_words = product_name.lower().split()

    for item in items:
        title = clean_text(item.get("title", ""))
        description = clean_text(item.get("description", ""))
        title_normalized = normalize(title)
        title_lower = title.lower()

        if any(word in title_lower for word in excluded_words):
            continue

        # 전체 상품명이 포함되거나 주요 단어가 일치하는 글
        matched_words = sum(
            normalize(word) in title_normalized
            for word in product_words
        )

        if (
            normalized_product not in title_normalized
            and matched_words < max(1, len(product_words) - 1)
        ):
            continue

        prices = extract_prices(title + " " + description)

        if not prices:
            continue

        # 하나의 게시글에서 여러 금액이 발견되면 제외
        if len(prices) != 1:
            continue

        price = prices[0]

        if price < 10000:
            continue

        valid_prices.append(price)
        matched_posts.append({
            "title": title,
            "price": price,
            "link": item.get("link", "")
        })

    if not valid_prices:
        return None, matched_posts

    median_price = statistics.median(valid_prices)

    filtered = [
        price for price in valid_prices
        if median_price * 0.5 <= price <= median_price * 1.5
    ]

    if not filtered:
        return None, matched_posts

    return round(statistics.median(filtered)), matched_posts
