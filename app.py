
import streamlit as st

from google import genai
from google.genai import types
import json

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

st.title("💰 AI 중고거래 가격 추천 시스템")
st.write("제품 정보와 판매 조건을 입력해 주세요.")

# 테스트용 제품별 기준 가격
prices = {
    "에어팟 프로 2": 140000,
    "에어팟 3": 80000,
    "갤럭시 버즈2 프로": 70000
}

product = st.selectbox(
    "1. 판매할 제품",
    list(prices.keys())
)

condition = st.selectbox(
    "2. 제품 상태",
    ["A등급 (매우 좋음)", "B등급 (보통)", "C등급 (사용감 많음)"]
)

period = st.selectbox(
    "3. 사용 기간",
    ["6개월 미만", "6개월~1년", "1년~2년", "2년 이상"]
)

accessories = st.checkbox("4. 박스와 구성품이 모두 있어요")

urgent = st.checkbox("5. 최대한 빨리 판매하고 싶어요")

st.subheader("📸 AI 제품 상태 분석")

uploaded_file = st.file_uploader(
    "판매할 제품의 사진을 업로드해 주세요",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    st.image(uploaded_file, caption="업로드한 제품 사진", width=300)

    if st.button("🤖 AI 사진 분석하기"):
        with st.spinner("Gemini AI가 제품 상태를 분석하고 있어요..."):
            try:
                image_bytes = uploaded_file.getvalue()

                response = client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=[
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type=uploaded_file.type
                        ),
                        """이 사진은 중고거래 상품의 사진입니다.
                        제품의 외관 상태를 분석하세요.

                        다음 기준으로 등급을 추천하세요.
                        A: 눈에 띄는 흠집이나 오염이 거의 없음
                        B: 가벼운 흠집이나 사용 흔적이 있음
                        C: 뚜렷한 흠집, 오염 또는 파손이 보임

                        사진에서 확인할 수 없는 기능적 결함은 추측하지 마세요.
                        반드시 다음 JSON 형식으로 답하세요.
                        {"grade": "A", "reason": "판단 근거"}"""
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )

                result = json.loads(response.text)
                grade = result["grade"]
                reason = result["reason"]

                st.session_state["ai_grade"] = grade

                st.success(f"AI 추천 상태 등급: {grade}등급")
                st.write(f"분석 근거: {reason}")
                st.info("사진만으로 배터리 상태나 내부 고장은 확인할 수 없습니다.")

            except Exception as e:
                st.error(f"AI 분석 중 오류가 발생했어요: {e}")

if st.button("💰 추천 판매 가격 확인"):
    price = prices[product]
    selected_grade = condition[0]
    final_grade = st.session_state.get("ai_grade", selected_grade)
    # 제품 상태 반영
    if final_grade == "B" :
        price *= 0.85
    elif final_grade == "C" :
        price *= 0.65

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
    st.write(f"제품 상태: {condition}")
    st.write(f"사용 기간: {period}")

    if urgent:
        st.info("빠른 판매를 위해 가격을 15% 낮췄어요.")

    st.caption("※ 현재는 테스트용 가상 시세와 감가율을 사용합니다.")


