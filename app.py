import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="لوحة متابعة المبيعات", page_icon="📊", layout="centered"
)

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.markdown(
    "<h1 style='text-align: center; color: #2C3E50;'>📊 مبيعات المحل"
    " المباشرة</h1>",
    unsafe_allow_html=True,
)
st.write("---")

store_id = st.text_input(
    "🔑 أدخل رمز أو معرف المحل الخاص بك:", placeholder="مثال: 1"
)

if store_id:
  with st.spinner("جاري جلب البيانات..."):
    try:
      response = (
          supabase.table("store_sales")
          .select("*")
          .eq("store_id", store_id)
          .order("last_update", desc=False)
          .execute()
      )
      data = response.data
    except Exception as e:
      st.error(f"حدث خطأ في الاتصال: {e}")
      data = []

  if data:
    df = pd.DataFrame(data)
    latest = df.iloc[-1]

    st.success(f"مرحباً بك! بيانات المتجر رقم: **{store_id}**")

    col1, col2 = st.columns(2)
    with col1:
      st.metric(
          label="💰 إجمالي المبيعات",
          value=f"{float(latest['total_sales']):,.2f} د.ل",
      )
    with col2:
      st.metric(
          label="🧾 عدد الفواتير", value=f"{int(latest['invoice_count'])}"
      )

    # عرض نوع العملية وطريقة الدفع بالتهجئة الصحيحة payment_method
    st.info(
        f"🏷️ **نوع العملية:** {latest.get('operation_type', 'مبيعات')}  \n💳"
        f" **طريقة الدفع:** {latest.get('payment_method', 'نقدي')}"
    )

    st.caption(f"🕒 آخر تحديث وصل من جهاز المحل: {latest['last_update']}")

    st.write("---")
    st.subheader("📈 مؤشر حركة المبيعات")

    if "last_update" in df.columns and "total_sales" in df.columns:
      df["last_update"] = pd.to_datetime(df["last_update"])
      chart_data = df.set_index("last_update")[["total_sales"]]
      st.line_chart(chart_data)

    if st.button("🔄 تحديث البيانات"):
      st.rerun()

  else:
    st.warning("⚠️ لم يتم العثور على بيانات لهذا المحل، تأكد من صحة الرمز.")
else:
  st.info("💡 أدخل رمز المحل في الخانة أعلاه لعرض لوحة بياناتك الخاصة.")

st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 12px;'>نظام متابعة"
    " المبيعات - مدعوم بـ Streamlit & Supabase</p>",
    unsafe_allow_html=True,
)