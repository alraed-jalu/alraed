from datetime import datetime, timedelta
import pandas as pd
import requests
import streamlit as st

# إعدادات الصفحة
st.set_page_config(
    page_title="متابعة مبيعات الوسام للتجهيزات المنزلية",
    page_icon="📊",
    layout="centered",
)

# إعدادات الاتصال بـ Supabase
SUPABASE_PROJECT_URL = "https://romlgjbchyrwlwpcgffi.supabase.co"
TABLE_NAME = "store_sales"
SUPABASE_URL = f"{SUPABASE_PROJECT_URL}/rest/v1/{TABLE_NAME}"
SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJvbWxnamJjaHlyd2x3cGNnZmZpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODY2MDMxNDUsImV4cCI6MjEwMjE3OTE0NX0.wg90ZMVaVMV1UAriGXNEhYqnWlCDzqFjZY87UqSTxbw"
)

STORE_ID = "1"

st.markdown(
    "<h2 style='text-align: center; color: #2c3e50;'>📊 تقارير مبيعات متجر"
    " الوسام</h2>",
    unsafe_allow_html=True,
)
st.markdown("---")


@st.cache_data(ttl=10)
def fetch_sales_data():
  headers = {
      "apikey": SUPABASE_KEY,
      "Authorization": f"Bearer {SUPABASE_KEY}",
      "Content-Type": "application/json",
  }
  url = f"{SUPABASE_URL}?store_id=eq.{STORE_ID}&order=last_update.desc"
  try:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
      data = response.json()
      if data:
        df = pd.DataFrame(data)
        if "last_update" in df.columns:
          df["last_update"] = pd.to_datetime(df["last_update"])
          df["date"] = df["last_update"].dt.date
        return df
  except Exception as e:
    st.error(f"❌ خطأ في الاتصال بقاعدة البيانات السحابية: {e}")
  return pd.DataFrame()


df = fetch_sales_data()

if df.empty:
  st.warning("⚠️ لا توجد بيانات مسجلة حالياً في السحابة لهذا المتجر.")
else:
  report_type = st.radio(
      "اختر نطاق التقرير:",
      ["تقرير اليوم", "تقرير الأسبوع الحالي", "تقرير الشهر الحالي"],
      horizontal=True,
  )

  invoice_filter = st.selectbox(
      "نوع عرض الفاتورة:",
      ["الكل (بيع وارجاع)", "بيع فقط", "ارجاع فقط"],
  )

  today = datetime.now().date()
  if report_type == "تقرير اليوم":
    filtered_df = df[df["date"] == today]
    period_title = "اليومي"
  elif report_type == "تقرير الأسبوع الحالي":
    start_of_week = today - timedelta(days=today.weekday())
    filtered_df = df[df["date"] >= start_of_week]
    period_title = "الأسبوعي"
  else:
    filtered_df = df[
        (df["last_update"].dt.month == today.month)
        & (df["last_update"].dt.year == today.year)
    ]
    period_title = "الشهري"

  if filtered_df.empty:
    st.info(f"ℹ️ لا توجد بيانات متاحة لهذا العرض ({report_type}).")
  else:
    latest_df = filtered_df.sort_values(
        by="last_update", ascending=False
    ).drop_duplicates(subset=["date"])

    total_invoices_sum = latest_df["invoice_count"].sum()

    c_sales = latest_df["cash_sales"].sum()
    c_returns = latest_df["cash_returns"].sum()

    m_sales = latest_df["mobicash_sales"].sum()
    m_returns = latest_df["mobicash_returns"].sum()

    card_s = latest_df["card_sales"].sum()
    card_r = latest_df["card_returns"].sum()

    y_sales = latest_df["yesserpay_sales"].sum()
    y_returns = latest_df["yesserpay_returns"].sum()

    e_sales = latest_df["edfaqli_sales"].sum()
    e_returns = latest_df["edfaqli_returns"].sum()

    if invoice_filter == "بيع فقط":
      cash_val = c_sales
      mobicash_val = m_sales
      card_val = card_s
      yesserpay_val = y_sales
      edfaqli_val = e_sales
      total_display = (
          cash_val + mobicash_val + card_val + yesserpay_val + edfaqli_val
      )
      filter_label = "إجمالي المبيعات (بدون المرتجعات)"
    elif invoice_filter == "ارجاع فقط":
      cash_val = c_returns
      mobicash_val = m_returns
      card_val = card_r
      yesserpay_val = y_returns
      edfaqli_val = e_returns
      total_display = (
          cash_val + mobicash_val + card_val + yesserpay_val + edfaqli_val
      )
      filter_label = "إجمالي المرتجعات فقط"
    else:
      cash_val = c_sales - c_returns
      mobicash_val = m_sales - m_returns
      card_val = card_s - card_r
      yesserpay_val = y_sales - y_returns
      edfaqli_val = e_sales - e_returns
      total_display = (
          cash_val + mobicash_val + card_val + yesserpay_val + edfaqli_val
      )
      filter_label = "إجمالي الصافي العام"

    st.subheader(f"📌 الملخص {period_title} ({invoice_filter})")
    col1, col2 = st.columns(2)
    col1.metric(filter_label, f"{total_display:,.2f} د.ل")
    col2.metric("عدد الفواتير الكلي", f"{total_invoices_sum:,}")

    st.markdown("---")

    payment_methods_data = {
        "طريقة الدفع": [
            "نقدي",
            "موبي كاش",
            "بطاقة مصرفية",
            "يسر باي",
            "ادفع لي",
        ],
        "المبلغ": [
            cash_val,
            mobicash_val,
            card_val,
            yesserpay_val,
            edfaqli_val,
        ],
    }
    chart_df = pd.DataFrame(payment_methods_data)

    st.subheader("📁 التفاصيل المالية حسب طرق الدفع")
    st.dataframe(chart_df, use_container_width=True)