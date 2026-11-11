from naver_search import get_market_prices
import streamlit as st
from market_compare import show_market_comparison
from google import genai
from google.genai import types
import json

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

st.title("💰 AI 중고거래 가격 추천 시스템")
st.write("제품 정보와 판매 조건을 입력해 주세요.")



product = st.text_input(
    "1. 판매할 제품명",
    placeholder="예: 아이폰 15 프로 256GB"
)

st.subheader("2. 외관 상태 평가")

evaluation_method = st.radio(
    "외관 상태를 평가할 방법을 선택해 주세요.",
    ["직접 선택", "AI 사진 분석"],
    horizontal=True
)

if evaluation_method == "직접 선택":
    condition = st.selectbox(
        "제품의 외관 상태",
        [
            "A등급 (매우 좋음)",
            "B등급 (보통)",
            "C등급 (사용감 많음)"
        ]
    )
else:
    condition = None


internal_condition = st.selectbox(
    "3. 내부 상태 (작동 상태)",
    [
        "정상 (모든 기능 정상 작동)",
        "성능 저하 (배터리 등 일부 성능 저하)",
        "기능 이상 (일부 기능 고장)",
        "확인 불가 (작동 상태 모름)"
    ]
)

period = st.selectbox(
    "4. 사용 기간",
    ["6개월 미만", "6개월~1년", "1년~2년", "2년 이상"]
)

accessories = st.checkbox("5. 박스와 구성품이 모두 있어요")

urgent = st.checkbox("6. 최대한 빨리 판매하고 싶어요")

if evaluation_method == "AI 사진 분석":
    st.subheader("📸 AI 제품 상태 분석")

    uploaded_files = st.file_uploader(
        "판매할 제품의 사진을 업로드해 주세요 (최소 2장 이상)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )

    if uploaded_files:
        st.image(
            uploaded_files,
            caption=[f"사진 {i + 1}" for i in range(len(uploaded_files))],
            width=200
        )

    if len(uploaded_files) < 2:
        st.warning("📷 사진을 최소 2장 이상 업로드해 주세요. (앞면, 뒷면, 옆면 등)")
    else:
        if st.button("🤖 AI 사진 분석하기"):
            with st.spinner(f"Gemini AI가 사진 {len(uploaded_files)}장을 분석하고 있어요..."):
                try:
                    image_parts = [
                        types.Part.from_bytes(
                            data=f.getvalue(),
                            mime_type=f.type
                        )
                        for f in uploaded_files
                    ]

                    response = client.models.generate_content(
                        model="gemini-3.5-flash",
                        contents=image_parts + [
                            f"""이 사진 {len(uploaded_files)}장은 같은 중고거래 상품을 여러 각도에서 찍은 사진입니다.
                            모든 사진을 종합해서 제품의 외관 상태를 분석하세요.
                            한 사진에서라도 흠집이나 파손이 보이면 등급에 반영하세요.

                            다음 기준으로 등급을 추천하세요.
                            A: 눈에 띄는 흠집이나 오염이 거의 없음
                            B: 가벼운 흠집이나 사용 흔적이 있음
                            C: 뚜렷한 흠집, 오염 또는 파손이 보임

                            사진에서 확인할 수 없는 기능적 결함은 추측하지 마세요.
                            반드시 다음 JSON 형식으로 답하세요.
                            {{"grade": "A", "reason": "판단 근거 (어느 사진에서 무엇이 보였는지 포함)"}}"""
                        ],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json"
                        )
                    )

                    result = json.loads(response.text)
                    grade = result["grade"]
                    reason = result["reason"]

                    if grade not in ["A", "B", "C"]:
                        raise ValueError("올바르지 않은 등급입니다.")

                    st.session_state["ai_grade"] = grade
                    st.session_state["ai_reason"] = reason

                except Exception:
                    st.warning(
                        "AI 분석을 완료하지 못했어요. "
                        "아래에서 직접 등급을 선택해 주세요."
                    )

        ai_grade = st.session_state.get("ai_grade")

        if ai_grade:
            st.success(f"AI 추천 외관 등급: {ai_grade}등급")
            st.write(
                "분석 근거:",
                st.session_state.get("ai_reason", "")
            )

    grade_options = ["A", "B", "C"]
    ai_grade = st.session_state.get("ai_grade", "B")

    condition = st.selectbox(
        "최종 외관 등급 (직접 수정 가능)",
        grade_options,
        index=grade_options.index(ai_grade),
        key="final_ai_grade"
    )

    st.info("사진만으로 배터리 상태나 내부 고장은 확인할 수 없습니다.")

if st.button("💰 추천 판매 가격 확인"):

    if not product.strip():
        st.warning("제품명을 입력해 주세요.")
        st.stop()

    with st.spinner("네이버 카페에서 중고 시세를 검색하고 있어요..."):
        try:
            market_price, matched_posts = get_market_prices(product.strip())
        except Exception as e:
            st.error("시세 검색 중 오류가 발생했어요.")
            st.error(str(e))
            st.stop()

    if market_price is None:
        st.warning(
            "신뢰할 만한 가격 자료가 충분하지 않아요. "
            "제품명을 더 정확하게 입력해 주세요."
        )
        st.stop()

    price = market_price

    st.info(f"검색된 게시글 기준 시세: {market_price:,}원")

    if evaluation_method == "직접 선택":
        final_grade = condition[0]
    else:
        final_grade = condition

    # 제품 상태 반영
    if final_grade == "B" :
        price *= 0.85
    elif final_grade == "C" :
        price *= 0.65

    # 내부 상태 반영
    if internal_condition.startswith("성능 저하"):
        price *= 0.90
    elif internal_condition.startswith("기능 이상"):
        price *= 0.70
    elif internal_condition.startswith("확인 불가"):
        price *= 0.85

    # 사용 기간 반영
    if period == "6개월~1년":
        price *= 0.95
    elif period == "1년~2년":
        price *= 0.90
    elif period == "2년 이상":
        price *= 0.80

    # 구성품 반영
    if not accessories:
        price *= 0.95

    # 급매 여부 반영
    if urgent:
        price *= 0.85

    price = round(price / 1000) * 1000

    st.success(f"추천 판매 가격: {price:,}원")
    st.write(f"제품명: {product}")
    st.write(f"제품 외관 상태: {final_grade}등급")
    st.write(f"제품 내부 상태: {internal_condition}")
    st.write(f"사용 기간: {period}")

    if urgent:
        st.info("빠른 판매를 위해 가격을 15% 낮췄어요.")

    st.caption("※ 네이버 카페 게시글에서 추출한 가격을 기준으로 계산합니다."
               "실제 거래 완료 가격이 아니며, 상태별 감가율은 테스트용 추정치입니다.")


    # 실제 검색 시세와 추천 판매가 비교
    st.subheader("📊 시세 비교")

    chart_data = {
        "검색 게시글 기준 시세": market_price,
        "추천 판매 가격": price
    }

    st.write("검색 게시글 기준 시세")
    st.progress(1.0)
    st.write(f"{market_price:,}원")

    st.write("추천 판매 가격")
    st.progress(min(price / market_price, 1.0))
    st.write(f"{price:,}원")

    # 검색에 사용된 게시글 표시
    st.subheader("🔎 시세 검색 근거")

    st.write(f"가격이 추출된 게시글: {len(matched_posts)}개")

    with st.expander("검색된 게시글 확인하기"):
        for post in matched_posts:
            st.write(f"**{post['title']}**")
            st.write(f"추출된 가격: {post['price']:,}원")

            if post["link"]:
                st.markdown(f"[게시글 바로가기]({post['link']})")

            st.divider()

    st.caption(
        "※ 검색 게시글에 표시된 가격을 바탕으로 계산한 "
        "참고용 추정 가격입니다. 실제 거래 완료 가격과 다를 수 있습니다."
    )
