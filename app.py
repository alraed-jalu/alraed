import os
from flask import Flask, Request, jsonify
from supabase import create_client, Client

app = Flask(__name__)
supabase: Client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

# خريطة الحسابات الثابتة لضمان دقة الأسماء وتجنب مشاكل الترميز
ACCOUNT_NAMES = {
    1: "زبون نقدي",
    2: "موبي كاش",
    3: "ادفع لي",
    4: "يسر باي",
    5: "بطاقة مصرفية"
}

@app.route("/")
def home():
    return "Alraed Bot is running perfectly!", 200

@app.route("/send-report", methods=["POST"])
def send_report():
    try:
        # جلب فواتير اليوم (تاريخ 2026-09-05) الغير محذوفة
        response = supabase.table("bills").select("account_id, amount_afetr_dis1").eq("bill_date", "2026-09-05").eq("deleted", 0).eq("removed", 0).execute()
        
        bills = response.data
        if not bills:
            return jsonify({"status": "no_bills_found"}), 200

        # تجميع المبالغ لكل حساب
        totals = {}
        for bill in bills:
            acc_id = bill.get("account_id")
            amount = float(bill.get("amount_afetr_dis1", 0) or 0)
            totals[acc_id] = totals.get(acc_id, 0.0) + amount

        # بناء نص التقرير بشكل منظم
        report_lines = ["📊 *التقرير المالي اليومي* - 2026-09-05\n"]
        grand_total = 0.0

        for acc_id, total in totals.items():
            name = ACCOUNT_NAMES.get(acc_id, f"حساب رقم {acc_id}")
            report_lines.append(f"* {name}: {total:.2f}")
            grand_total += total

        report_lines.append(f"\n💰 *الإجمالي الكلي*: {grand_total:.2f} د.ل")
        final_report = "\n".join(report_lines)

        return jsonify({
            "status": "success",
            "calculated_totals": totals,
            "report_text": final_report
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
