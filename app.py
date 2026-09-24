from datetime import datetime, timedelta
import pandas as pd
import requests
import streamlit as st
from supabase import create_client

# إعدادات الصفحة
st.set_page_config(
    page_title="متابعة مبيعات المتاجر - منظومة الرائد",
    page_icon="📊",
    layout="centered",
)

# إعدادات الاتصال بـ Supabase
SUPABASE_PROJECT_URL = "https://romlgjbchyrwlwpcgffi.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJvbWxnamJjaHlyd2x3cGNnZmZpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODY2MDMxNDUsImV4cCI6MjEwMjE3OTE0NX0.wg90ZMVaVMV1UAriGXNEhYqnWlCDzqFjZY87UqSTxbw"

# تهيئة اتصال Supabase بشكل آمن
@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_PROJECT_URL, SUPABASE_KEY)

supabase = init_supabase()

# دالة للتحقق من بيانات المحل (اسم المستخدم والرقم السري)
def verify_store_credentials(username, password):
    try:
        response = supabase.table("stores").select("*").eq("username", username).execute()
        if response.data and len(response.data) > 0:
            store_info = response.data[0]
            if store_info.get("password") == password:
                return store_info
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال بقاعدة بيانات التحقق: {e}")
    return None

# إدارة حالة الجلسة لتسجيل الدخول
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.store_data = None

# 1. شاشة تسجيل الدخول
if not st.session_state.authenticated:
    st.markdown("<h2 style='text-align: center; color: #2c3e50;'>🔐 تسجيل دخول لوحة التحكم</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    with st.form("login_form"):
        username_input = st.text_input("اسم المستخدم الخاص بالمحل")
        password_input = st.text_input("الرقم السري", type="password")
        submit_button = st.form_submit_button("تسجيل الدخول")
        
        if submit_button:
            store_record = verify_store_credentials(username_input, password_input)
            if store_record:
                st.session_state.authenticated = True
                st.session_state.store_data = store_record
                st.success("تم تسجيل الدخول بنجاح! جاري تحميل لوحة التحكم...")
                st.rerun()
            else:
                st.error("⚠️ اسم المستخدم أو الرقم السري غير صحيح. يرجى المحاولة مرة أخرى.")

else:
    # 2. واجهة التحكم بعد تسجيل الدخول بنجاح
    current_store = st.session_state.store_data
    STORE_NAME = current_store.get("store_name", "المتجر")
    STORE_ID = str(current_store.get("store_id", "1"))
    TABLE_NAME = "store_sales"

    # الشريط الجانبي للإدارة والتحكم
    st.sidebar.markdown(f"👤 مرحببك بك: **{STORE_NAME}**")
    st.sidebar.markdown("---")

    # زر التحديث اللحظي للبيانات
    if st.sidebar.button("🔄 تحديث البيانات اللحظية"):
        st.cache_data.clear()
        st.success("تم تحديث البيانات بنجاح!")
        st.rerun()

    # زر تسجيل الخروج
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.authenticated = False
        st.session_state.store_data = None
        st.rerun()

    st.markdown(
        f"<h2 style='text-align: center; color: #2c3e50;'>📊 تقارير مبيعات متجر: {STORE_NAME}</h2>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # دالة جلب البيانات مع منع التخزين المؤقت الطويل لضمان جلب الجديد فوراً
    def fetch_sales_data(store_id):
      try:
        response = supabase.table(TABLE_NAME).select("*").eq("store_id", store_id).order("last_update", desc=True).execute()
        data = response.data
        if data:
          df = pd.DataFrame(data)
          if "last_update" in df.columns:
            df["last_update"] = pd.to_datetime(df["last_update"])
            df["date"] = df["last_update"].dt.date
          return df
      except Exception as e:
        st.error(f"❌ خطأ في جلب بيانات المبيعات: {e}")
      return pd.DataFrame()

    df = fetch_sales_data(STORE_ID)

    if df.empty:
      st.warning(f"⚠️ لا توجد بيانات مسجلة حالياً في السحابة لهذا المتجر ({STORE_NAME}).")
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