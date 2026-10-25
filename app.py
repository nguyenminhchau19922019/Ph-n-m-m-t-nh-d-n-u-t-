import streamlit as st
import pandas as pd
import math

# ==================================================
# 1. CẤU HÌNH TRANG
# ==================================================
st.set_page_config(
    page_title="Phân tích hiệu quả dự án đầu tư",
    page_icon="📊",
    layout="wide"
)

st.title("📊 PHÂN TÍCH HIỆU QUẢ DỰ ÁN ĐẦU TƯ")
st.caption(
    "Tính toán NPV, IRR, MIRR, PI, PP và DPP "
    "từ dòng tiền dự kiến của dự án."
)

st.info(
    "Nhập số liệu theo cùng một đơn vị tiền tệ. "
    "Dòng tiền thu vào nhập số dương; dòng tiền chi ra nhập số âm."
)


# ==================================================
# 2. HÀM ĐỊNH DẠNG
# ==================================================
def format_money(value):
    if value is None or not math.isfinite(value):
        return "Không xác định"
    return f"{value:,.2f}"


def format_rate(value):
    if value is None or not math.isfinite(value):
        return "Không xác định"
    return f"{value * 100:.2f}%"


def format_year(value):
    if value is None or not math.isfinite(value):
        return "Chưa hoàn vốn"
    return f"{value:.2f} năm"


# ==================================================
# 3. HÀM TÍNH NPV
# ==================================================
def calculate_npv(rate, cash_flows):
    return sum(
        cf / (1 + rate) ** year
        for year, cf in enumerate(cash_flows)
    )


# ==================================================
# 4. HÀM TÍNH IRR
# ==================================================
def calculate_irr(cash_flows):
    if not any(cf > 0 for cf in cash_flows):
        return None

    if not any(cf < 0 for cf in cash_flows):
        return None

    def npv_at_rate(rate):
        try:
            return calculate_npv(rate, cash_flows)
        except (OverflowError, ZeroDivisionError):
            return float("nan")

    # Khảo sát các khoảng lãi suất để tìm nghiệm đổi dấu
    rates = [
        -0.9999, -0.99, -0.95, -0.90, -0.80,
        -0.60, -0.40, -0.20, 0.0,
        0.01, 0.05, 0.10, 0.15, 0.20, 0.30,
        0.50, 0.75, 1.0, 1.5, 2.0, 3.0,
        5.0, 10.0, 20.0, 50.0, 100.0
    ]

    previous_rate = rates[0]
    previous_npv = npv_at_rate(previous_rate)

    for rate in rates:
        current_npv = npv_at_rate(rate)

        if (
            math.isfinite(current_npv)
            and abs(current_npv) < 1e-10
        ):
            return rate

        if (
            math.isfinite(previous_npv)
            and math.isfinite(current_npv)
            and previous_npv * current_npv < 0
        ):
            low = previous_rate
            high = rate
            low_npv = previous_npv

            for _ in range(300):
                mid = (low + high) / 2
                mid_npv = npv_at_rate(mid)

                if not math.isfinite(mid_npv):
                    return None

                if abs(mid_npv) < 1e-10:
                    return mid

                if low_npv * mid_npv < 0:
                    high = mid
                else:
                    low = mid
                    low_npv = mid_npv

            return (low + high) / 2

        previous_rate = rate
        previous_npv = current_npv

    return None


# ==================================================
# 5. HÀM TÍNH MIRR
# ==================================================
def calculate_mirr(cash_flows, finance_rate, reinvest_rate):
    periods = len(cash_flows) - 1

    if periods <= 0:
        return None

    if not any(cf < 0 for cf in cash_flows):
        return None

    if not any(cf > 0 for cf in cash_flows):
        return None

    # Giá trị hiện tại của dòng tiền âm
    pv_costs = sum(
        abs(cf) / (1 + finance_rate) ** year
        for year, cf in enumerate(cash_flows)
        if cf < 0
    )

    # Giá trị tương lai của dòng tiền dương
    fv_benefits = sum(
        cf * (1 + reinvest_rate) ** (periods - year)
        for year, cf in enumerate(cash_flows)
        if cf > 0
    )

    if pv_costs <= 0 or fv_benefits <= 0:
        return None

    return (fv_benefits / pv_costs) ** (1 / periods) - 1


# ==================================================
# 6. HÀM TÍNH PP VÀ DPP
# ==================================================
def calculate_payback(cash_flows, discount_rate=0.0):
    cumulative = cash_flows[0]

    # Vốn đầu tư ban đầu không âm
    if cumulative >= 0:
        return 0.0

    for year in range(1, len(cash_flows)):
        discounted_cf = (
            cash_flows[year] / (1 + discount_rate) ** year
        )

        previous_cumulative = cumulative
        cumulative += discounted_cf

        if cumulative >= 0 and discounted_cf > 0:
            return (
                year - 1
                + abs(previous_cumulative) / discounted_cf
            )

    return None


# ==================================================
# 7. NHẬP THÔNG TIN DỰ ÁN
# ==================================================
st.subheader("1. Thông tin dự án")

col1, col2, col3 = st.columns(3)

with col1:
    don_vi = st.selectbox(
        "Đơn vị tiền tệ",
        ["Triệu đồng", "Tỷ đồng", "Nghìn đồng", "Đồng"]
    )

with col2:
    so_nam = st.number_input(
        "Số năm dự án",
        min_value=1,
        max_value=20,
        value=5,
        step=1
    )

with col3:
    von_dau_tu = st.number_input(
        "Vốn đầu tư ban đầu",
        min_value=0.01,
        value=1000.0,
        step=100.0,
        format="%.2f"
    )


# ==================================================
# 8. NHẬP DÒNG TIỀN THEO ĐÚNG THỨ TỰ NĂM
# ==================================================
st.subheader("2. Nhập dòng tiền từng năm")

st.write(
    "Các ô được sắp xếp lần lượt từ Năm 1 đến Năm "
    f"{int(so_nam)}. Khi thay đổi số năm, bảng sẽ cập nhật."
)

gia_tri_mau = [-200.0, -100.0, 300.0, 800.0, 1200.0]

# Tạo tiêu đề cột theo đúng thứ tự năm
tieu_de = st.columns(int(so_nam))

for year in range(int(so_nam)):
    with tieu_de[year]:
        st.markdown(f"**Năm {year + 1}**")

# Tạo ô nhập dòng tiền theo thứ tự trái sang phải
cac_cot_dong_tien = st.columns(int(so_nam))
cash_flows = []

for year in range(int(so_nam)):
    default_value = (
        gia_tri_mau[year]
        if year < len(gia_tri_mau)
        else 0.0
    )

    with cac_cot_dong_tien[year]:
        cf = st.number_input(
            f"Dòng tiền năm {year + 1}",
            value=float(default_value),
            step=100.0,
            format="%.2f",
            key=f"dong_tien_nam_{year + 1}"
        )

    cash_flows.append(cf)

st.caption(
    "Ví dụ: -200 ở Năm 1 nghĩa là dự án phát sinh dòng tiền chi "
    "200 trong năm đầu tiên. Số liệu sẽ không tự chuyển sang năm khác."
)


# ==================================================
# 9. NHẬP TỶ LỆ CHIẾT KHẤU
# ==================================================
st.subheader("3. Thông số tài chính")

col1, col2 = st.columns(2)

with col1:
    discount_rate_pct = st.number_input(
        "Tỷ lệ chiết khấu (%)",
        min_value=0.0,
        max_value=1000.0,
        value=20.0,
        step=1.0
    )

with col2:
    reinvest_rate_pct = st.number_input(
        "Tỷ lệ tái đầu tư dùng cho MIRR (%)",
        min_value=0.0,
        max_value=1000.0,
        value=20.0,
        step=1.0
    )

st.caption(
    "MIRR sử dụng tỷ lệ chiết khấu làm tỷ lệ tài trợ "
    "và tỷ lệ tái đầu tư được nhập riêng."
)


# ==================================================
# 10. TÍNH TOÁN
# ==================================================
rate = discount_rate_pct / 100
reinvest_rate = reinvest_rate_pct / 100

# Năm 0 là vốn đầu tư ban đầu, tự động mang dấu âm
full_cash_flows = [-float(von_dau_tu)] + cash_flows

npv = calculate_npv(rate, full_cash_flows)
irr = calculate_irr(full_cash_flows)

mirr = calculate_mirr(
    full_cash_flows,
    rate,
    reinvest_rate
)

# PI = PV dòng tiền dương / PV toàn bộ dòng tiền âm
pv_benefits = sum(
    cf / (1 + rate) ** year
    for year, cf in enumerate(full_cash_flows)
    if cf > 0
)

pv_costs = sum(
    abs(cf) / (1 + rate) ** year
    for year, cf in enumerate(full_cash_flows)
    if cf < 0
)

pi = pv_benefits / pv_costs if pv_costs > 0 else None

# PP: không chiết khấu
pp = calculate_payback(full_cash_flows, 0.0)

# DPP: có chiết khấu
dpp = calculate_payback(full_cash_flows, rate)


# ==================================================
# 11. HIỂN THỊ KẾT QUẢ
# ==================================================
st.divider()
st.subheader("4. Kết quả phân tích dự án")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "NPV",
        f"{format_money(npv)} {don_vi}"
    )

    st.metric("IRR", format_rate(irr))

with col2:
    st.metric("MIRR", format_rate(mirr))

    st.metric(
        "PI",
        f"{pi:.4f}" if pi is not None else "Không xác định"
    )

with col3:
    st.metric("PP", format_year(pp))

    st.metric("DPP", format_year(dpp))


# ==================================================
# 12. ĐÁNH GIÁ SƠ BỘ
# ==================================================
st.subheader("5. Nhận xét hiệu quả dự án")

if npv > 0:
    st.success(
        "NPV > 0: Dự án tạo ra giá trị hiện tại ròng dương "
        "theo tỷ lệ chiết khấu đã chọn."
    )
elif npv < 0:
    st.warning(
        "NPV < 0: Dự án chưa đạt mức sinh lời yêu cầu "
        "theo tỷ lệ chiết khấu đã chọn."
    )
else:
    st.info(
        "NPV = 0: Giá trị hiện tại dòng tiền thu vào "
        "bằng giá trị hiện tại dòng tiền chi ra."
    )

if irr is not None:
    if irr > rate:
        st.success(
            "IRR cao hơn tỷ lệ chiết khấu. Với dòng tiền thông thường "
            "và nghiệm IRR duy nhất, kết quả này ủng hộ dự án."
        )
    elif irr < rate:
        st.warning(
            "IRR thấp hơn tỷ lệ chiết khấu đã chọn."
        )
    else:
        st.info("IRR bằng tỷ lệ chiết khấu.")
else:
    st.warning(
        "Không tìm được IRR trong khoảng khảo sát. "
        "Dòng tiền có thể không có nghiệm hoặc có nhiều nghiệm."
    )

if pi is not None:
    if pi > 1:
        st.success("PI > 1: Giá trị hiện tại dòng tiền dương lớn hơn dòng tiền âm.")
    elif pi < 1:
        st.warning("PI < 1: Giá trị hiện tại dòng tiền dương nhỏ hơn dòng tiền âm.")
    else:
        st.info("PI = 1: Hai giá trị hiện tại bằng nhau.")

if pp is None:
    st.write("**PP:** Dự án chưa hoàn vốn trong thời gian dự báo.")
else:
    st.write(f"**PP:** Hoàn vốn sau khoảng {format_year(pp)}.")

if dpp is None:
    st.write("**DPP:** Dự án chưa hoàn vốn có chiết khấu trong thời gian dự báo.")
else:
    st.write(f"**DPP:** Hoàn vốn có chiết khấu sau khoảng {format_year(dpp)}.")


# ==================================================
# 13. BẢNG DÒNG TIỀN CHI TIẾT
# ==================================================
st.subheader("6. Bảng dòng tiền theo từng năm")

rows = []
cumulative_cf = 0.0
cumulative_pv = 0.0

for year, cf in enumerate(full_cash_flows):
    discount_factor = 1 / (1 + rate) ** year
    pv = cf * discount_factor

    cumulative_cf += cf
    cumulative_pv += pv

    rows.append({
        "Năm": year,
        "Dòng tiền": round(cf, 4),
        "Hệ số chiết khấu": round(discount_factor, 6),
        "Giá trị hiện tại": round(pv, 4),
        "Lũy kế dòng tiền": round(cumulative_cf, 4),
        "Lũy kế giá trị hiện tại": round(cumulative_pv, 4)
    })

df = pd.DataFrame(rows)

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)

# ==================================================
# 14. TẢI KẾT QUẢ
# ==================================================
st.subheader("7. Xuất dữ liệu")

col1, col2 = st.columns(2)

with col1:
    st.download_button(
        "⬇️ Tải bảng dòng tiền CSV",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name="bang_dong_tien_du_an.csv",
        mime="text/csv",
        use_container_width=True
    )

with col2:
    ket_qua = pd.DataFrame({
        "Chỉ tiêu": ["NPV", "IRR", "MIRR", "PI", "PP", "DPP"],
        "Kết quả": [
            f"{format_money(npv)} {don_vi}",
            format_rate(irr),
            format_rate(mirr),
            f"{pi:.4f}" if pi is not None else "Không xác định",
            format_year(pp),
            format_year(dpp)
        ]
    })

    st.download_button(
        "⬇️ Tải kết quả phân tích CSV",
        data=ket_qua.to_csv(index=False).encode("utf-8-sig"),
        file_name="ket_qua_du_an.csv",
        mime="text/csv",
        use_container_width=True
    )


# ==================================================
# 15. GIẢI THÍCH CÔNG THỨC
# ==================================================
with st.expander("📘 Giải thích các chỉ tiêu tài chính"):
    st.markdown(
        """
        **1. NPV – Giá trị hiện tại thuần**

        Tổng giá trị hiện tại của các dòng tiền, bao gồm vốn đầu tư
        tại Năm 0. NPV dương cho thấy dự án tạo giá trị theo tỷ lệ
        chiết khấu được chọn.

        **2. IRR – Tỷ suất hoàn vốn nội bộ**

        Là tỷ lệ chiết khấu làm NPV bằng 0. Với dòng tiền đổi dấu
        nhiều lần, có thể tồn tại nhiều nghiệm hoặc không có nghiệm.

        **3. MIRR – Tỷ suất hoàn vốn nội bộ điều chỉnh**

        Xem xét tỷ lệ tài trợ cho dòng tiền âm và tỷ lệ tái đầu tư
        cho dòng tiền dương.

        **4. PI – Chỉ số sinh lời**

        PI = Giá trị hiện tại dòng tiền dương /
        Giá trị hiện tại toàn bộ dòng tiền âm.

        **5. PP – Thời gian hoàn vốn**

        Thời gian cần để dòng tiền tích lũy chưa chiết khấu bù đắp
        các khoản chi đầu tư.

        **6. DPP – Thời gian hoàn vốn có chiết khấu**

        Thời gian cần để dòng tiền tích lũy sau chiết khấu bù đắp
        các khoản chi đầu tư.

        Lưu ý: PP và DPP giả định nội suy dòng tiền trong năm
        hoàn vốn. Khi so sánh dự án, nên xem xét NPV cùng các
        chỉ tiêu khác thay vì chỉ dựa vào thời gian hoàn vốn.
        """
    )

st.caption(
    "Ứng dụng phục vụ học tập và phân tích sơ bộ. "
    "Kết quả phụ thuộc vào độ chính xác của dòng tiền và các giả định."
    )
