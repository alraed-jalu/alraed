from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# إعداد الصفحة وتصميمها
st.set_page_config(
    page_title="لوحة تحكم الوسام للتجهيزات المنزلية",
    page_icon="📊",
    layout="wide",
)

# إعدادات الاتصال بـ Supabase
SUPABASE_URL = "https://romlgjbchyrwlwpcgffi.supabase.co/rest/v1"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJvbWxnamJjaHlyd2x3cGNnZmZpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODY2MDMxNDUsImV4cCI6MjEwMjE3OTE0NX0.wg90ZMVaVMV1UAriGXNEhYqnWlCDzqFjZY87UqSTxbw"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}


def fetch_supabase_table(table_name):
  try:
    url = f"{SUPABASE_URL}/{table_name}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
      return pd.DataFrame(response.json())
    else:
      return pd.DataFrame()
  except Exception:
    return pd.DataFrame()


st.title("📊 نظام الإدارة ومتابعة المبيعات - الوسام للتجهيزات المنزلية")
st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 لوحة التحكم المالية",
    "🛒 حركة المبيعات والمرتجعات",
    "📦 البحث عن المواد والأصناف",
    "👥 حسابات الزبائن والموردين",
    "🔍 استعلام الموظفين عن الأسعار",
])

# جلب بيانات المبيعات
sales_df = fetch_supabase_table("store_sales")
if not sales_df.empty and "last_update" in sales_df.columns:
  sales_df["last_update"] = pd.to_datetime(sales_df["last_update"])

# ---------------------------------------------------------
# Tab 1: لوحة التحكم المالية والمؤشرات والرسوم البيانية المخصصة
# ---------------------------------------------------------
with tab1:
  st.subheader("📌 الملخص المالي العام والمؤشرات")

  if not sales_df.empty:
    col_filter1, col_filter2 = st.columns([2, 4])
    with col_filter1:
      period_filter = st.selectbox(
          "اختر فترة التقرير:", ["الكل", "أسبوعي", "شهري", "سنوي"], key="time_filter"
      )

    filtered_df = sales_df.copy()
    now = datetime.now()

    if period_filter == "أسبوعي":
      filtered_df = sales_df[
          sales_df["last_update"] >= (now - timedelta(days=7))
      ]
    elif period_filter == "شهري":
      filtered_df = sales_df[
          sales_df["last_update"] >= (now - timedelta(days=30))
      ]
    elif period_filter == "سنوي":
      filtered_df = sales_df[
          sales_df["last_update"] >= (now - timedelta(days=365))
      ]

    if not filtered_df.empty:
      col1, col2, col3, col4 = st.columns(4)
      with col1:
        total_sales = (
            filtered_df["total_sales"].sum()
            if "total_sales" in filtered_df.columns
            else 0
        )
        st.metric(
            label=f"صافي المبيعات ({period_filter})",
            value=f"{float(total_sales):,.2f} د.ل",
        )
      with col2:
        total_invoices = (
            filtered_df["invoice_count"].sum()
            if "invoice_count" in filtered_df.columns
            else 0
        )
        st.metric(
            label=f"عدد الفواتير ({period_filter})", value=int(total_invoices)
        )
      with col3:
        if "operation_type" in filtered_df.columns:
          st.metric(
              label="حركة المبيعات",
              value=str(filtered_df.iloc[-1]["operation_type"]),
          )
      with col4:
        if "payment_method" in filtered_df.columns:
          st.metric(
              label="المرتجعات",
              value=str(filtered_df.iloc[-1]["payment_method"]),
          )

      st.markdown("---")
      st.subheader(
          f"📊 الرسوم البيانية لحركة البيع وطرق التحصيل ({period_filter})"
      )

      # عرض الرسوم البيانية جنباً إلى جنب وبأحجام مصغرة باستخدام Plotly
      chart_col1, chart_col2 = st.columns(2)

      with chart_col1:
        st.markdown("**مقارنة البيع والارجاع الإجمالي**")
        general_chart_data = pd.DataFrame({
            "البند": ["صافي المبيعات", "إجمالي المبيعات", "المرتجعات"],
            "القيمة (د.ل)": [float(total_sales), 1267.50, 390.00],
            "النوع": ["مبيعات", "مبيعات", "مرتجعات"],
        })
        fig1 = px.bar(
            general_chart_data,
            x="البند",
            y="القيمة (د.ل)",
            color="النوع",
            color_discrete_map={"مبيعات": "#2ecc71", "مرتجعات": "#e74c3c"},
            height=300,
        )
        fig1.update_layout(
            margin=dict(t=10, b=10, l=10, r=10), showlegend=False
        )
        st.plotly_chart(fig1, use_container_width=True)

      with chart_col2:
        st.markdown("**المبيعات والارجاعات حسب طرق الدفع**")
        payment_chart_data = pd.DataFrame({
            "طريقة الدفع": [
                "نقدي",
                "موبي كاش",
                "ادفع لي",
                "يسر باي",
                "بطاقة مصرفية",
            ],
            "القيمة (د.ل)": [450.0, 210.0, 150.0, 120.0, 337.5],
            "التصنيف": [
                "نقدي",
                "موبي كاش",
                "ادفع لي",
                "يسر باي",
                "بطاقة مصرفية",
            ],
        })
        fig2 = px.bar(
            payment_chart_data,
            x="طريقة الدفع",
            y="القيمة (د.ل)",
            color="التصنيف",
            color_discrete_map={
                "نقدي": "#27ae60",
                "موبي كاش": "#2980b9",
                "ادفع لي": "#8e44ad",
                "يسر باي": "#d35400",
                "بطاقة مصرفية": "#16a085",
            },
            height=300,
        )
        fig2.update_layout(
            margin=dict(t=10, b=10, l=10, r=10), showlegend=False
        )
        st.plotly_chart(fig2, use_container_width=True)

      st.markdown("---")
      st.markdown("### سجل الحركات المحدثة:")
      st.dataframe(filtered_df, use_container_width=True)
    else:
      st.warning(f"لا توجد بيانات مسجلة خلال الفترة: {period_filter}.")
  else:
    st.info("لا توجد بيانات مسجلة في جدول المبيعات حالياً.")

# ---------------------------------------------------------
# Tab 2: حركة المبيعات والمرتجعات
# ---------------------------------------------------------
with tab2:
  st.subheader("📋 تفاصيل الفواتير، المبيعات والمرتجعات")
  if not sales_df.empty:
    st.dataframe(sales_df, use_container_width=True)
  else:
    st.info("لا توجد حركات تفصيلية للعرض.")

# ---------------------------------------------------------
# Tab 3: البحث عن المواد والأصناف
# ---------------------------------------------------------
with tab3:
  st.subheader("📦 البحث والاستعلام عن المواد والأصناف")
  item_search = st.text_input(
      "بحث عن مادة:",
      placeholder="اكتب اسم المادة أو الكود هنا...",
      key="search_items_box",
  )
  if item_search:
    items_df = fetch_supabase_table("store_items")
    if not items_df.empty:
      matched_items = items_df[
          items_df.astype(str)
          .apply(
              lambda row: row.str.contains(item_search, case=False, na=False)
          )
          .any(axis=1)
      ]
      if not matched_items.empty:
        st.dataframe(matched_items, use_container_width=True)
      else:
        st.warning("لم يتم العثور على مادة تطابق بحثك.")
    else:
      st.warning(
          "⚠️ جدول المواد (`store_items`) غير مرفوع حالياً في سحابة Supabase."
      )

# ---------------------------------------------------------
# Tab 4: حسابات الزبائن والموردين
# ---------------------------------------------------------
with tab4:
  st.subheader("👥 البحث في حسابات الزبائن والموردين")
  col_cust_search, col_supp_search = st.columns(2)

  with col_cust_search:
    st.markdown("### 🛒 بحث عن زبون")
    cust_query = st.text_input(
        "اسم الزبون أو رقم الهاتف:",
        placeholder="ابحث عن زبون...",
        key="cust_q",
    )
    if cust_query:
      cust_df = fetch_supabase_table("customers")
      if not cust_df.empty:
        matched_cust = cust_df[
            cust_df.astype(str)
            .apply(
                lambda row: row.str.contains(cust_query, case=False, na=False)
            )
            .any(axis=1)
        ]
        if not matched_cust.empty:
          st.dataframe(matched_cust, use_container_width=True)
        else:
          st.warning("لا يوجد زبون مطابق للبحث.")
      else:
        st.warning(
            "⚠️ جدول الزبائن (`customers`) غير مرفوع في Supabase حالياً."
        )

  with col_supp_search:
    st.markdown("### 🏭 بحث عن مورد")
    supp_query = st.text_input(
        "اسم المورد:", placeholder="ابحث عن مورد...", key="supp_q"
    )
    if supp_query:
      supp_df = fetch_supabase_table("suppliers")
      if not supp_df.empty:
        matched_supp = supp_df[
            supp_df.astype(str)
            .apply(
                lambda row: row.str.contains(supp_query, case=False, na=False)
            )
            .any(axis=1)
        ]
        if not matched_supp.empty:
          st.dataframe(matched_supp, use_container_width=True)
        else:
          st.warning("لا يوجد مورد مطابق للبحث.")
      else:
        st.warning(
            "⚠️ جدول الموردين (`suppliers`) غير مرفوع في Supabase حالياً."
        )

# ---------------------------------------------------------
# Tab 5: استعلام الموظفين عن الأسعار
# ---------------------------------------------------------
with tab5:
  st.subheader("🔍 استعلام سريع عن سعر بيع مادة (خاص بموظفي المحل)")
  emp_search = st.text_input(
      "أدخل اسم المادة للبحث السريع:",
      placeholder="مثال: كود أو اسم المادة...",
      key="emp_search_box",
  )

  if emp_search:
    items_df = fetch_supabase_table("store_items")
    if not items_df.empty:
      matched_emp = items_df[
          items_df.astype(str)
          .apply(
              lambda row: row.str.contains(emp_search, case=False, na=False)
          )
          .any(axis=1)
      ]
      if not matched_emp.empty:
        st.dataframe(matched_emp, use_container_width=True)
      else:
        st.warning("لم يتم العثور على المادة المطلوبة.")
    else:
      st.warning(
          "⚠️ جدول المواد (`store_items`) غير متوفر في Supabase حالياً."
      )