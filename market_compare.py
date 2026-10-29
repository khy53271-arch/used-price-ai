"""중고 시세 비교 기능 - 팀 프로젝트 독립 모듈.

실제 거래 데이터가 아닌 시연용 예시 가격을 사용합니다.
기존 app.py에서 import하여 호출하거나, 이 파일을 단독 실행할 수 있습니다.
"""
import streamlit as st

# 제품별 참고 가격 목록 (원) - 실제 시세가 아닌 예시 데이터
MARKET_PRICES = {
    "에어팟 프로 2": [120000, 130000, 140000, 150000, 160000],
    "에어팟 3": [65000, 75000, 80000, 85000, 95000],
    "갤럭시 버즈2 프로": [55000, 65000, 70000, 75000, 85000],
}


def show_market_comparison(product=None, ai_price=None):
    """중고 시세 비교 화면을 표시합니다.

    Args:
        product: 기존 앱에서 선택한 제품명. 생략 시 사용자가 직접 선택합니다.
        ai_price: 기존 앱에서 계산한 추천 가격(원). 생략 시 직접 입력합니다.
    """
    st.subheader("📊 중고 시세 비교")
    st.caption("※ 참고 시세는 시연용 가상 데이터이며, 실시간 중고거래 시세가 아닙니다.")

    if product is None:
        product = st.selectbox("비교할 제품", list(MARKET_PRICES), key="market_product")
    if product not in MARKET_PRICES:
        st.warning("선택한 제품의 참고 시세 데이터가 없습니다.")
        return

    if ai_price is None:
        ai_price = st.number_input(
            "추천 판매 가격(원)",
            min_value=0,
            value=MARKET_PRICES[product][2],
            step=1000,
            key="market_ai_price",
        )
    try:
        ai_price = float(ai_price)
    except (ValueError, TypeError):
        st.error("추천 가격은 숫자여야 합니다.")
        return
    if ai_price < 0:
        st.error("추천 가격은 0원 이상이어야 합니다.")
        return

    values = MARKET_PRICES[product]
    low, high = min(values), max(values)
    average = sum(values) / len(values)
    difference = ai_price - average

    c1, c2, c3 = st.columns(3)
    c1.metric("최저 참고 시세", f"{low:,.0f}원")
    c2.metric("평균 참고 시세", f"{average:,.0f}원")
    c3.metric("최고 참고 시세", f"{high:,.0f}원")
    st.metric("추천 판매 가격", f"{ai_price:,.0f}원",
              delta=f"{difference:+,.0f}원 (평균 대비)",
              delta_color="off")

    if difference > 0:
        st.warning(f"추천 가격이 평균 참고 시세보다 {difference:,.0f}원 높습니다.")
    elif difference < 0:
        st.info(f"추천 가격이 평균 참고 시세보다 {abs(difference):,.0f}원 낮습니다.")
    else:
        st.success("추천 가격이 평균 참고 시세와 같습니다.")

    st.markdown("#### 💰 가격 비교")

    percent = (ai_price - average) / average * 100 if average else 0

    if percent < 0:
        st.success(f"평균 시세보다 {abs(percent):.1f}% 저렴해요!")
    elif percent > 0:
        st.warning(f"평균 시세보다 {percent:.1f}% 높아요!")
    else:
        st.info("평균 시세와 동일한 가격이에요.")

    max_price = max(ai_price, average, 1)
    ai_width = ai_price / max_price * 100
    avg_width = average / max_price * 100

    st.write(f"🟢 추천 판매 가격: **{ai_price:,.0f}원**")
    st.progress(
        min(ai_price / max_price, 1.0)
    )

    st.write(f"⚪ 평균 참고 시세: **{average:,.0f}원**")
    st.progress(
        min(average / max_price, 1.0)
    )
  
if __name__ == "__main__":
    st.title("💰 중고 시세 비교 기능")
    show_market_comparison()