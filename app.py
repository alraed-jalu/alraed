from datetime import datetime, timedelta
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
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

# إدارة حالة الجلسة لتسجيل الدخول
if "authenticated" not in st.session_state:
  st.session_state.authenticated = False
  st.session_state.user_type = None
  st.session_state.store_data = None
  st.session_state.staff_data = None

# 1. شاشة تسجيل الدخول العامة
if not st.session_state.authenticated:
  st.markdown(
      "<h2 style='text-align: center; color: #2c3e50;'>🔐 تسجيل دخول لوحة"
      " التحكم</h2>",
      unsafe_allow_html=True,
  )
  st.markdown("---")

  login_mode = st.radio(
      "اختر نوع الدخول:", ["صاحب المحل (الإدارة)", "موظف (بحث أسعار البيع)"], horizontal=True
  )

  with st.form("login_form"):
    username_input = st.text_input("اسم المستخدم")
    password_input = st.text_input("الرقم السري", type="password")
    submit_button = st.form_submit_button("تسجيل الدخول")

    if submit_button:
      if login_mode == "صاحب المحل (الإدارة)":
        try:
          response = (
              supabase.table("stores")
              .select("*")
              .eq("username", username_input)
              .execute()
          )
          if response.data and len(response.data) > 0:
            store_info = response.data[0]
            if store_info.get("password") == password_input:
              st.session_state.authenticated = True
              st.session_state.user_type = "owner"
              st.session_state.store_data = store_info
              st.success("تم تسجيل الدخول بنجاح كمدير للمتجر!")
              st.rerun()
            else:
              st.error("⚠️ الرقم السري للإدارة غير صحيح.")
          else:
            st.error("⚠️ اسم المستخدم للإدارة غير صحيح.")
        except Exception as e:
          st.error(f"❌ خطأ في الاتصال: {e}")
      else:
        staff_found = False
        try:
          response = (
              supabase.table("staff_users")
              .select("*")
              .eq("username", username_input)
              .execute()
          )
          if response.data and len(response.data) > 0:
            staff_info = response.data[0]
            if staff_info.get("password") == password_input:
              st.session_state.authenticated = True
              st.session_state.user_type = "staff"
              st.session_state.staff_data = staff_info
              staff_found = True
              st.success("تم تسجيل الدخول بنجاح كموظف!")
              st.rerun()
        except Exception:
          pass

        if not staff_found:
          default_staff_list = [
              {"username": "سمارت", "password": "1234", "store_id": "1"},
        {"username": "سنتر", "password": "1234", "store_id": "2"},
        {"username": "المتميزة", "password": "1234", "store_id": "3"},


          ]
          for staff in default_staff_list:
            if (
                username_input == staff["username"]
                and password_input == staff["password"]
            ):
              st.session_state.authenticated = True
              st.session_state.user_type = "staff"
              st.session_state.staff_data = staff
              staff_found = True
              st.success("تم تسجيل الدخول بنجاح كموظف!")
              st.rerun()

          if not staff_found:
            st.error("⚠️ اسم المستخدم أو الرقم السري للموظف غير صحيح.")

else:
  # -------------------------------------------------------------
  # أ) واجهة الموظف (بحث مباشر وسريع بالاسم أو الباركود + الكاميرا المباشرة)
  # -------------------------------------------------------------
  if st.session_state.user_type == "staff":
    staff_info = st.session_state.staff_data
    staff_store_id = str(staff_info.get("store_id", "2"))

    if st.sidebar.button("🚪 تسجيل الخروج"):
      st.session_state.authenticated = False
      st.session_state.user_type = None
      st.session_state.staff_data = None
      st.rerun()

    st.markdown(
        f"<h2 style='text-align: center; color: #2c3e50;'>🔍 استعلام أسعار"
        f" المبيعات (المحل رقم: {staff_store_id})</h2>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    use_camera = st.checkbox("📷 تفعيل ماسح الباركود بالكاميرا المباشرة")

    if use_camera:
      st.markdown(
          "<p style='text-align: center; color: #7f8c8d; font-size: 14px;'>قم"
          " بتوجيه كاميرا الهاتف نحو الباركود لقراءته والبحث عنه تلقائياً 👇</p>",
          unsafe_allow_html=True,
      )
      barcode_scanner_html = """
            <div style="text-align: center; background: #f1f2f6; padding: 10px; border-radius: 10px;">
                <div id="reader" style="width: 100%; max-width: 350px; margin: auto;"></div>
                <p id="scan_result" style="color: #27ae60; font-weight: bold; margin-top: 8px; font-size: 16px;"></p>
            </div>
            <script src="https://unpkg.com/html5-qrcode"></script>
            <script>
                function onScanSuccess(decodedText, decodedResult) {
                    document.getElementById('scan_result').innerText = "تم المسح بنجاح: " + decodedText;
                    const inputs = window.parent.document.querySelectorAll('input[type="text"]');
                    if (inputs.length > 0) {
                        const targetInput = inputs[0];
                        targetInput.value = decodedText;
                        targetInput.dispatchEvent(new Event('input', { bubbles: true }));
                        targetInput.dispatchEvent(new Event('change', { bubbles: true }));
                        targetInput.dispatchEvent(new KeyboardEvent('keydown', {
                            key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true
                        }));
                    }
                }
                const html5QrCode = new Html5Qrcode("reader");
                html5QrCode.start(
                    { facingMode: "environment" },
                    { fps: 10, qrbox: { width: 250, height: 100 } },
                    onScanSuccess
                ).catch(err => { console.error(err); });
            </script>
            """
      components.html(barcode_scanner_html, height=320)

    search_query = st.text_input(
        "🔎 ابحث باسم الصنف أو أدخل/ألصق الباركود:",
        placeholder="اكتب اسم الصنف أو امسح الباركود هنا...",
    )

    if search_query:
      try:
        query = (
            supabase.table("store_items")
            .select("item_name, sale_price, available_qty, barcode, item_id")
            .eq("store_id", staff_store_id)
        )

        if str(search_query).isdigit():
          query = query.or_(
              f"barcode.eq.{search_query},item_id.eq.{int(search_query)}"
          )
        else:
          query = query.ilike("item_name", f"%{search_query}%")

        response = query.execute()
        items_data = response.data

        if items_data:
          st.markdown(
              f"<p style='color: #27ae60;'><b>تم العثور على {len(items_data)}"
              " صنف:</b></p>",
              unsafe_allow_html=True,
          )
          for item in items_data:
            st.markdown(
                f"""
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #dcdde1; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <h4 style="color: #2c3e50; margin: 0 0 10px 0;">📦 {item.get('item_name')} <span style="font-size: 13px; color: #7f8c8d;">(الباركود: {item.get('barcode')})</span></h4>
                    <div style="display: flex; justify-content: space-between; font-size: 16px;">
                        <span>💰 سعر البيع: <b style="color: #27ae60; font-size: 18px;">{item.get('sale_price')} د.ل</b></span>
                        <span>📦 الكمية المتاحة: <b style="color: #2980b9; font-size: 18px;">{item.get('available_qty')}</b></span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
          st.info("ℹ️ لا توجد أصناف مطابقة لهذا البحث أو الباركود.")
      except Exception as e:
        st.error(f"❌ حدث خطأ أثناء البحث: {e}")
    else:
      st.markdown(
          "<p style='text-align: center; color: #7f8c8d; margin-top: 30px;'>قم"
          " بكتابة اسم الصنف، أو تفعيل الكاميرا، أو استخدام قارئ الباركود"
          " للاستعلام الفوري 👆</p>",
          unsafe_allow_html=True,
      )

  # -------------------------------------------------------------
  # ب) واجهة صاحب المحل (تقارير المبيعات + إدارة الأصناف والمخزون)
  # -------------------------------------------------------------
  else:
    current_store = st.session_state.store_data
    STORE_NAME = current_store.get("store_name", "المتجر")
    STORE_ID = str(current_store.get("store_id", "1"))
    TABLE_NAME = "store_sales"

    if st.sidebar.button("🚪 تسجيل الخروج"):
      st.session_state.authenticated = False
      st.session_state.user_type = None
      st.session_state.store_data = None
      st.rerun()

    st.markdown(
        f"<h2 style='text-align: center; color: #2c3e50;'>📊 لوحة تحكم متجر:"
        f" {STORE_NAME}</h2>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    tab_sales, tab_inventory = st.tabs(["📈 تقارير المبيعات", "📦 إدارة الأصناف والمخزون"])

    with tab_sales:
      col_refresh, col_empty = st.columns([1, 2])
      with col_refresh:
        if st.button("🔄 تحديث البيانات اللحظية"):
          st.cache_data.clear()
          st.success("تم تحديث البيانات بنجاح!")
          st.rerun()

      st.markdown("---")

      try:
        sales_response = (
            supabase.table(TABLE_NAME)
            .select("*")
            .eq("store_id", STORE_ID)
            .order("last_update", desc=True)
            .execute()
        )
        sales_data = sales_response.data
        df = pd.DataFrame(sales_data) if sales_data else pd.DataFrame()
        if not df.empty and "last_update" in df.columns:
          df["last_update"] = pd.to_datetime(df["last_update"])
          df["date"] = df["last_update"].dt.date
      except Exception as e:
        st.error(f"❌ خطأ في جلب بيانات المبيعات: {e}")
        df = pd.DataFrame()

      if df.empty:
        st.warning(
            f"⚠️ لا توجد بيانات مبيعات مسجلة حالياً في السحابة لهذا المتجر"
            f" ({STORE_NAME})."
        )
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
          latest_df = (
              filtered_df.sort_values(by="last_update", ascending=False)
              .drop_duplicates(subset=["date"])
          )

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
            cash_val, mobicash_val, card_val, yesserpay_val, edfaqli_val = (
                c_sales,
                m_sales,
                card_s,
                y_sales,
                e_sales,
            )
            filter_label = "إجمالي المبيعات (بدون المرتجعات)"
          elif invoice_filter == "ارجاع فقط":
            cash_val, mobicash_val, card_val, yesserpay_val, edfaqli_val = (
                c_returns,
                m_returns,
                card_r,
                y_returns,
                e_returns,
            )
            filter_label = "إجمالي المرتجعات فقط"
          else:
            cash_val = c_sales - c_returns
            mobicash_val = m_sales - m_returns
            card_val = card_s - card_r
            yesserpay_val = y_sales - y_returns
            edfaqli_val = e_sales - e_returns
            filter_label = "إجمالي الصافي العام"

          total_display = (
              cash_val + mobicash_val + card_val + yesserpay_val + edfaqli_val
          )

          st.subheader(f"📌 الملخص {period_title} ({invoice_filter})")
          col1, col2 = st.columns(2)
          col1.metric(filter_label, f"{total_display:,.2f} د.ل")
          col2.metric("عدد الفواتير الكلي", f"{total_invoices_sum:,}")

          st.markdown("---")

          chart_df = pd.DataFrame({
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
          })

          st.subheader("📁 التفاصيل المالية حسب طرق الدفع")
          st.dataframe(chart_df, use_container_width=True)

    with tab_inventory:
      st.subheader("📦 البحث المباشر في مخزون وأصناف المتجر")
      item_search = st.text_input(
          "🔎 ابحث باسم الصنف أو أدخل/ألصق الباركود في المخزن:",
          placeholder="اكتب اسم الصنف أو الباركود هنا...",
          key="owner_item_search",
      )

      if item_search:
        try:
          inv_query = (
              supabase.table("store_items")
              .select(
                  "item_id, item_name, buy_price, sale_price, available_qty,"
                  " barcode, last_update"
              )
              .eq("store_id", STORE_ID)
          )

          if str(item_search).isdigit():
            inv_query = inv_query.or_(
                f"barcode.eq.{item_search},item_id.eq.{int(item_search)}"
            )
          else:
            inv_query = inv_query.ilike("item_name", f"%{item_search}%")

          inv_response = inv_query.execute()
          inv_data = inv_response.data

          if inv_data:
            st.markdown(
                f"<p style='color: #27ae60;'><b>تم العثور على {len(inv_data)}"
                " صنف:</b></p>",
                unsafe_allow_html=True,
            )
            for item in inv_data:
              st.markdown(
                  f"""
                  <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #dcdde1; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                      <h4 style="color: #2c3e50; margin: 0 0 10px 0;">📦 {item.get('item_name')} <span style="font-size: 13px; color: #7f8c8d;">(الباركود: {item.get('barcode')})</span></h4>
                      <div style="display: flex; justify-content: space-between; font-size: 15px; flex-wrap: wrap; gap: 10px;">
                          <span>🛒 سعر الشراء: <b style="color: #e67e22;">{item.get('buy_price')} د.ل</b></span>
                          <span>💰 سعر البيع: <b style="color: #27ae60; font-size: 17px;">{item.get('sale_price')} د.ل</b></span>
                          <span>📦 الكمية المتاحة: <b style="color: #2980b9; font-size: 17px;">{item.get('available_qty')}</b></span>
                      </div>
                  </div>
                  """,
                  unsafe_allow_html=True,
              )
          else:
            st.info("ℹ️ لا توجد أصناف مطابقة لهذا البحث في مخزون هذا المتجر.")
        except Exception as e:
          st.error(f"❌ حدث خطأ أثناء البحث في المخزون: {e}")
      else:
        st.markdown(
            "<p style='text-align: center; color: #7f8c8d; margin-top: 30px;'>قم"
            " بكتابة اسم الصنف أو مسح الباركود للبحث في أصناف ومخزون المتجر 👆</p>",
            unsafe_allow_html=True,
        )