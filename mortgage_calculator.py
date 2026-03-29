"""
住宅ローン計算アプリ (Mortgage Calculator)
Windows用 Python/tkinter アプリケーション
"""

import tkinter as tk
from tkinter import ttk, messagebox
import math


def calculate_monthly_payment(principal: float, annual_rate: float, months: int) -> float:
    """元利均等返済の月返済額を計算する"""
    if annual_rate == 0:
        return principal / months
    monthly_rate = annual_rate / 100 / 12
    return principal * monthly_rate * (1 + monthly_rate) ** months / ((1 + monthly_rate) ** months - 1)


def build_amortization_schedule(principal: float, annual_rate: float, months: int):
    """返済スケジュール（元利均等）を生成する"""
    schedule = []
    balance = principal
    monthly_rate = annual_rate / 100 / 12
    payment = calculate_monthly_payment(principal, annual_rate, months)

    for month in range(1, months + 1):
        if annual_rate == 0:
            interest = 0.0
        else:
            interest = balance * monthly_rate
        principal_part = payment - interest
        balance -= principal_part
        if balance < 0:
            balance = 0.0
        schedule.append((month, payment, principal_part, interest, balance))
    return schedule


class MortgageCalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("住宅ローン計算アプリ")
        self.resizable(True, True)
        self.configure(bg="#f0f4f8")
        self._build_ui()

    def _build_ui(self):
        # ---- タイトル ----
        title_frame = tk.Frame(self, bg="#2b6cb0", pady=12)
        title_frame.pack(fill="x")
        tk.Label(
            title_frame,
            text="住宅ローン計算アプリ",
            font=("Yu Gothic UI", 16, "bold"),
            bg="#2b6cb0",
            fg="white",
        ).pack()

        # ---- 入力フレーム ----
        input_frame = tk.LabelFrame(
            self,
            text="ローン条件の入力",
            font=("Yu Gothic UI", 10, "bold"),
            bg="#f0f4f8",
            fg="#2d3748",
            padx=16,
            pady=12,
        )
        input_frame.pack(fill="x", padx=20, pady=(16, 8))

        fields = [
            ("借入金額（万円）", "loan_amount", "3000"),
            ("年利（%）", "interest_rate", "1.5"),
            ("返済期間（年）", "loan_years", "35"),
            ("ボーナス返済月数（年2回）", "bonus_months", "0"),
            ("ボーナス返済額（万円/回）", "bonus_amount", "0"),
        ]

        self.vars = {}
        for label_text, key, default in fields:
            row = tk.Frame(input_frame, bg="#f0f4f8")
            row.pack(fill="x", pady=4)
            tk.Label(row, text=label_text, width=24, anchor="w",
                     font=("Yu Gothic UI", 10), bg="#f0f4f8", fg="#4a5568").pack(side="left")
            var = tk.StringVar(value=default)
            self.vars[key] = var
            entry = tk.Entry(row, textvariable=var, width=16,
                             font=("Yu Gothic UI", 10), relief="solid", bd=1)
            entry.pack(side="left", padx=(8, 0))

        # ---- 計算ボタン ----
        btn_frame = tk.Frame(self, bg="#f0f4f8")
        btn_frame.pack(pady=8)
        calc_btn = tk.Button(
            btn_frame,
            text="計算する",
            command=self._calculate,
            font=("Yu Gothic UI", 11, "bold"),
            bg="#2b6cb0",
            fg="white",
            activebackground="#2c5282",
            activeforeground="white",
            relief="flat",
            padx=24,
            pady=8,
            cursor="hand2",
        )
        calc_btn.pack()

        # ---- 結果フレーム ----
        self.result_frame = tk.LabelFrame(
            self,
            text="計算結果",
            font=("Yu Gothic UI", 10, "bold"),
            bg="#f0f4f8",
            fg="#2d3748",
            padx=16,
            pady=12,
        )
        self.result_frame.pack(fill="x", padx=20, pady=(0, 8))

        self.result_labels = {}
        result_keys = [
            ("月返済額", "monthly_payment"),
            ("総返済額", "total_payment"),
            ("うち利息総額", "total_interest"),
            ("元本に対する利息割合", "interest_ratio"),
        ]
        for label_text, key in result_keys:
            row = tk.Frame(self.result_frame, bg="#f0f4f8")
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label_text, width=22, anchor="w",
                     font=("Yu Gothic UI", 10), bg="#f0f4f8", fg="#4a5568").pack(side="left")
            lbl = tk.Label(row, text="---", font=("Yu Gothic UI", 10, "bold"),
                           bg="#f0f4f8", fg="#2b6cb0", anchor="w")
            lbl.pack(side="left", padx=(8, 0))
            self.result_labels[key] = lbl

        # ---- 返済スケジュール ----
        sched_frame = tk.LabelFrame(
            self,
            text="返済スケジュール（元利均等）",
            font=("Yu Gothic UI", 10, "bold"),
            bg="#f0f4f8",
            fg="#2d3748",
            padx=8,
            pady=8,
        )
        sched_frame.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        cols = ("月", "月返済額（円）", "元本（円）", "利息（円）", "残高（円）")
        self.tree = ttk.Treeview(sched_frame, columns=cols, show="headings", height=12)
        col_widths = [60, 120, 110, 100, 130]
        for col, w in zip(cols, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="e")
        self.tree.column("月", anchor="center")

        scrollbar_y = ttk.Scrollbar(sched_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar_y.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")

        # 年単位表示切替
        toggle_frame = tk.Frame(self, bg="#f0f4f8")
        toggle_frame.pack(pady=(0, 8))
        self.show_yearly = tk.BooleanVar(value=False)
        tk.Checkbutton(
            toggle_frame,
            text="年単位で表示",
            variable=self.show_yearly,
            command=self._refresh_schedule,
            font=("Yu Gothic UI", 9),
            bg="#f0f4f8",
            fg="#4a5568",
        ).pack()

        self._schedule_cache = []

    def _get_float(self, key: str) -> float:
        try:
            return float(self.vars[key].get().replace(",", ""))
        except ValueError:
            raise ValueError(f"'{key}' の入力値が正しくありません。数値を入力してください。")

    def _calculate(self):
        try:
            principal_man = self._get_float("loan_amount")   # 万円
            annual_rate = self._get_float("interest_rate")   # %
            years = self._get_float("loan_years")             # 年
            bonus_months_count = int(self._get_float("bonus_months"))  # 年n回
            bonus_amount_man = self._get_float("bonus_amount")        # 万円/回

            if principal_man <= 0:
                raise ValueError("借入金額は0より大きい値を入力してください。")
            if annual_rate < 0:
                raise ValueError("年利は0以上の値を入力してください。")
            if years <= 0:
                raise ValueError("返済期間は0より大きい値を入力してください。")

        except ValueError as e:
            messagebox.showerror("入力エラー", str(e))
            return

        principal = principal_man * 10000
        months = int(years * 12)

        monthly_payment = calculate_monthly_payment(principal, annual_rate, months)
        schedule = build_amortization_schedule(principal, annual_rate, months)
        self._schedule_cache = schedule

        # ボーナス返済分（簡易：総額に加算）
        bonus_total = bonus_amount_man * 10000 * bonus_months_count * years

        total_regular = monthly_payment * months
        total_payment = total_regular + bonus_total
        total_interest = total_payment - principal
        interest_ratio = (total_interest / principal * 100) if principal > 0 else 0

        self.result_labels["monthly_payment"].config(
            text=f"{monthly_payment:,.0f} 円"
        )
        self.result_labels["total_payment"].config(
            text=f"{total_payment:,.0f} 円 ({total_payment / 10000:,.1f} 万円)"
        )
        self.result_labels["total_interest"].config(
            text=f"{total_interest:,.0f} 円 ({total_interest / 10000:,.1f} 万円)"
        )
        self.result_labels["interest_ratio"].config(
            text=f"{interest_ratio:.1f} %"
        )

        self._refresh_schedule()

    def _refresh_schedule(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        if not self._schedule_cache:
            return

        if self.show_yearly.get():
            yearly = {}
            for month, payment, principal_part, interest, balance in self._schedule_cache:
                year = math.ceil(month / 12)
                if year not in yearly:
                    yearly[year] = [0.0, 0.0, 0.0, balance]
                yearly[year][0] += payment
                yearly[year][1] += principal_part
                yearly[year][2] += interest
                yearly[year][3] = balance

            for year, (pay, prin, intr, bal) in yearly.items():
                tag = "even" if year % 2 == 0 else "odd"
                self.tree.insert(
                    "", "end",
                    values=(f"{year}年目", f"{pay:,.0f}", f"{prin:,.0f}", f"{intr:,.0f}", f"{bal:,.0f}"),
                    tags=(tag,),
                )
        else:
            for i, (month, payment, principal_part, interest, balance) in enumerate(self._schedule_cache):
                tag = "even" if i % 2 == 0 else "odd"
                self.tree.insert(
                    "", "end",
                    values=(month, f"{payment:,.0f}", f"{principal_part:,.0f}", f"{interest:,.0f}", f"{balance:,.0f}"),
                    tags=(tag,),
                )

        self.tree.tag_configure("odd", background="#edf2f7")
        self.tree.tag_configure("even", background="#ffffff")


def main():
    app = MortgageCalculatorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
