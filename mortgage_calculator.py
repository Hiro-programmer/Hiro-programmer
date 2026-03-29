"""
住宅ローン計算アプリ (Mortgage Calculator) - 拡張版
Windows用 Python/tkinter アプリケーション

機能:
  - 元利均等返済の計算
  - 返済スケジュール（月次/年次）
  - CSV出力
  - 複数プラン比較（最大4プラン）
  - 残高推移グラフ
"""

import csv
import math
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# matplotlib はオプション（なくてもグラフタブ以外は動作する）
try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.ticker as mticker
    matplotlib.rcParams["font.family"] = ["Yu Gothic", "Meiryo", "sans-serif"]
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

# ─────────────────────────────────────────
#  計算ロジック
# ─────────────────────────────────────────

def monthly_payment(principal: float, annual_rate: float, months: int) -> float:
    """元利均等返済の月返済額"""
    if annual_rate == 0:
        return principal / months
    r = annual_rate / 100 / 12
    return principal * r * (1 + r) ** months / ((1 + r) ** months - 1)


def amortization_schedule(principal: float, annual_rate: float, months: int):
    """返済スケジュール: [(月, 返済額, 元本, 利息, 残高), ...]"""
    schedule = []
    balance = principal
    r = annual_rate / 100 / 12
    pmt = monthly_payment(principal, annual_rate, months)
    for m in range(1, months + 1):
        interest = balance * r if annual_rate != 0 else 0.0
        prin = pmt - interest
        balance = max(balance - prin, 0.0)
        schedule.append((m, pmt, prin, interest, balance))
    return schedule


def yearly_summary(schedule):
    """月次スケジュールを年次にまとめる"""
    yearly = {}
    for month, pmt, prin, intr, bal in schedule:
        yr = math.ceil(month / 12)
        if yr not in yearly:
            yearly[yr] = [0.0, 0.0, 0.0, bal]
        yearly[yr][0] += pmt
        yearly[yr][1] += prin
        yearly[yr][2] += intr
        yearly[yr][3] = bal
    return yearly


# ─────────────────────────────────────────
#  共通ウィジェット
# ─────────────────────────────────────────

BLUE   = "#2b6cb0"
BLUE2  = "#2c5282"
BG     = "#f0f4f8"
FG     = "#2d3748"
FG2    = "#4a5568"
WHITE  = "#ffffff"
STRIPE = "#edf2f7"

FONT      = ("Yu Gothic UI", 10)
FONT_BOLD = ("Yu Gothic UI", 10, "bold")
FONT_LG   = ("Yu Gothic UI", 14, "bold")


def labeled_entry(parent, text, var, width=14):
    row = tk.Frame(parent, bg=BG)
    row.pack(fill="x", pady=3)
    tk.Label(row, text=text, width=26, anchor="w",
             font=FONT, bg=BG, fg=FG2).pack(side="left")
    e = tk.Entry(row, textvariable=var, width=width,
                 font=FONT, relief="solid", bd=1)
    e.pack(side="left", padx=(6, 0))
    return e


def result_row(parent, label):
    row = tk.Frame(parent, bg=BG)
    row.pack(fill="x", pady=3)
    tk.Label(row, text=label, width=22, anchor="w",
             font=FONT, bg=BG, fg=FG2).pack(side="left")
    lbl = tk.Label(row, text="---", font=FONT_BOLD, bg=BG, fg=BLUE, anchor="w")
    lbl.pack(side="left", padx=(8, 0))
    return lbl


def make_treeview(parent, cols, widths, height=12):
    frame = tk.Frame(parent, bg=BG)
    frame.pack(fill="both", expand=True)
    tree = ttk.Treeview(frame, columns=cols, show="headings", height=height)
    for col, w in zip(cols, widths):
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor="e" if col != cols[0] else "center")
    sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    tree.tag_configure("odd",  background=STRIPE)
    tree.tag_configure("even", background=WHITE)
    return tree


# ─────────────────────────────────────────
#  メインアプリ
# ─────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("住宅ローン計算アプリ")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._build_ui()

    def _build_ui(self):
        # タイトルバー
        hdr = tk.Frame(self, bg=BLUE, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="住宅ローン計算アプリ",
                 font=FONT_LG, bg=BLUE, fg=WHITE).pack()

        # タブ
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=12, pady=10)

        self.tab_single   = SingleTab(nb)
        self.tab_compare  = CompareTab(nb)
        if HAS_MPL:
            self.tab_graph = GraphTab(nb)

        nb.add(self.tab_single,  text="  計算・スケジュール  ")
        nb.add(self.tab_compare, text="  複数プラン比較  ")
        if HAS_MPL:
            nb.add(self.tab_graph, text="  グラフ  ")


# ─────────────────────────────────────────
#  タブ1: 計算 + スケジュール
# ─────────────────────────────────────────

class SingleTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self._schedule = []
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=16, pady=(12, 0))

        # 入力
        inp = tk.LabelFrame(top, text="ローン条件", font=FONT_BOLD,
                            bg=BG, fg=FG, padx=12, pady=10)
        inp.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self.v = {k: tk.StringVar(value=d) for k, d in [
            ("loan_amount",   "3000"),
            ("interest_rate", "1.5"),
            ("loan_years",    "35"),
            ("bonus_months",  "0"),
            ("bonus_amount",  "0"),
        ]}
        labeled_entry(inp, "借入金額（万円）",       self.v["loan_amount"])
        labeled_entry(inp, "年利（%）",              self.v["interest_rate"])
        labeled_entry(inp, "返済期間（年）",          self.v["loan_years"])
        labeled_entry(inp, "ボーナス返済（年何回）",  self.v["bonus_months"])
        labeled_entry(inp, "ボーナス返済額（万円/回）",self.v["bonus_amount"])

        tk.Button(inp, text="計算する", command=self._calc,
                  font=FONT_BOLD, bg=BLUE, fg=WHITE,
                  activebackground=BLUE2, activeforeground=WHITE,
                  relief="flat", padx=20, pady=6, cursor="hand2").pack(pady=(10, 0))

        # 結果
        res = tk.LabelFrame(top, text="計算結果", font=FONT_BOLD,
                             bg=BG, fg=FG, padx=12, pady=10)
        res.pack(side="left", fill="both", expand=True)

        self.r = {
            "monthly":  result_row(res, "月返済額"),
            "total":    result_row(res, "総返済額"),
            "interest": result_row(res, "うち利息総額"),
            "ratio":    result_row(res, "利息割合"),
        }

        # スケジュール
        sched = tk.LabelFrame(self, text="返済スケジュール（元利均等）",
                               font=FONT_BOLD, bg=BG, fg=FG, padx=8, pady=8)
        sched.pack(fill="both", expand=True, padx=16, pady=(10, 4))

        cols    = ("月", "返済額（円）", "元本（円）", "利息（円）", "残高（円）")
        widths  = [60, 120, 110, 100, 130]
        self.tree = make_treeview(sched, cols, widths, height=14)

        # 下ツールバー
        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", padx=16, pady=(0, 10))

        self.yearly_var = tk.BooleanVar(value=False)
        tk.Checkbutton(bar, text="年単位で表示", variable=self.yearly_var,
                       command=self._refresh, font=FONT, bg=BG, fg=FG2).pack(side="left")

        tk.Button(bar, text="CSVで保存", command=self._export_csv,
                  font=FONT, bg="#276749", fg=WHITE,
                  activebackground="#22543d", activeforeground=WHITE,
                  relief="flat", padx=14, pady=4, cursor="hand2").pack(side="right")

    def _flt(self, key):
        try:
            return float(self.v[key].get().replace(",", ""))
        except ValueError:
            raise ValueError(f"「{key}」の値が正しくありません。")

    def _calc(self):
        try:
            p_man  = self._flt("loan_amount")
            rate   = self._flt("interest_rate")
            years  = self._flt("loan_years")
            b_cnt  = int(self._flt("bonus_months"))
            b_man  = self._flt("bonus_amount")
            if p_man <= 0: raise ValueError("借入金額は0より大きい値を入力してください。")
            if rate  < 0:  raise ValueError("年利は0以上の値を入力してください。")
            if years <= 0: raise ValueError("返済期間は0より大きい値を入力してください。")
        except ValueError as e:
            messagebox.showerror("入力エラー", str(e)); return

        principal = p_man * 10000
        months    = int(years * 12)
        pmt       = monthly_payment(principal, rate, months)
        self._schedule = amortization_schedule(principal, rate, months)

        bonus_total  = b_man * 10000 * b_cnt * years
        total        = pmt * months + bonus_total
        total_int    = total - principal
        ratio        = total_int / principal * 100 if principal else 0

        self.r["monthly"].config( text=f"{pmt:,.0f} 円")
        self.r["total"].config(   text=f"{total:,.0f} 円  ({total/10000:,.1f} 万円)")
        self.r["interest"].config(text=f"{total_int:,.0f} 円  ({total_int/10000:,.1f} 万円)")
        self.r["ratio"].config(   text=f"{ratio:.1f} %")
        self._refresh()

    def _refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        if not self._schedule:
            return
        if self.yearly_var.get():
            for i, (yr, (pay, prin, intr, bal)) in enumerate(yearly_summary(self._schedule).items()):
                tag = "even" if i % 2 == 0 else "odd"
                self.tree.insert("", "end",
                    values=(f"{yr}年目", f"{pay:,.0f}", f"{prin:,.0f}", f"{intr:,.0f}", f"{bal:,.0f}"),
                    tags=(tag,))
        else:
            for i, (m, pmt, prin, intr, bal) in enumerate(self._schedule):
                tag = "even" if i % 2 == 0 else "odd"
                self.tree.insert("", "end",
                    values=(m, f"{pmt:,.0f}", f"{prin:,.0f}", f"{intr:,.0f}", f"{bal:,.0f}"),
                    tags=(tag,))

    def _export_csv(self):
        if not self._schedule:
            messagebox.showwarning("CSV出力", "先に計算してください。"); return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV ファイル", "*.csv"), ("すべてのファイル", "*.*")],
            initialfile="返済スケジュール.csv",
        )
        if not path:
            return
        use_yearly = self.yearly_var.get()
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            if use_yearly:
                writer.writerow(["年", "返済額合計（円）", "元本合計（円）", "利息合計（円）", "残高（円）"])
                for yr, (pay, prin, intr, bal) in yearly_summary(self._schedule).items():
                    writer.writerow([f"{yr}年目", f"{pay:.0f}", f"{prin:.0f}", f"{intr:.0f}", f"{bal:.0f}"])
            else:
                writer.writerow(["月", "返済額（円）", "元本（円）", "利息（円）", "残高（円）"])
                for m, pmt, prin, intr, bal in self._schedule:
                    writer.writerow([m, f"{pmt:.0f}", f"{prin:.0f}", f"{intr:.0f}", f"{bal:.0f}"])
        messagebox.showinfo("CSV出力完了", f"保存しました:\n{path}")


# ─────────────────────────────────────────
#  タブ2: 複数プラン比較
# ─────────────────────────────────────────

PLAN_COLORS = ["#2b6cb0", "#276749", "#9b2c2c", "#6b46c1"]
PLAN_NAMES  = ["プラン A", "プラン B", "プラン C", "プラン D"]

class CompareTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self._plans = []   # 計算済みプランのキャッシュ
        self._build()

    def _build(self):
        # プラン入力エリア（横スクロール対応）
        top_wrap = tk.Frame(self, bg=BG)
        top_wrap.pack(fill="x", padx=12, pady=(10, 0))

        inp_label = tk.Label(top_wrap, text="各プランの条件を入力してください（空欄のプランは無視されます）",
                             font=FONT, bg=BG, fg=FG2)
        inp_label.pack(anchor="w", pady=(0, 6))

        plan_row = tk.Frame(top_wrap, bg=BG)
        plan_row.pack(fill="x")

        self.plan_vars = []
        FIELDS = [
            ("借入金額（万円）", "amount",   "3000"),
            ("年利（%）",        "rate",     "1.5"),
            ("返済期間（年）",    "years",    "35"),
            ("プラン名",         "name",     ""),
        ]
        for i in range(4):
            pf = tk.LabelFrame(plan_row, text=PLAN_NAMES[i],
                               font=FONT_BOLD, bg=BG,
                               fg=PLAN_COLORS[i], padx=10, pady=8)
            pf.pack(side="left", fill="both", expand=True, padx=(0, 8 if i < 3 else 0))
            vd = {}
            for label, key, default in FIELDS:
                vd[key] = tk.StringVar(value=default if i == 0 else "")
                r = tk.Frame(pf, bg=BG)
                r.pack(fill="x", pady=2)
                tk.Label(r, text=label, width=16, anchor="w",
                         font=FONT, bg=BG, fg=FG2).pack(side="left")
                tk.Entry(r, textvariable=vd[key], width=10,
                         font=FONT, relief="solid", bd=1).pack(side="left", padx=(4, 0))
            self.plan_vars.append(vd)

        # 比較ボタン
        tk.Button(top_wrap, text="比較する", command=self._compare,
                  font=FONT_BOLD, bg=BLUE, fg=WHITE,
                  activebackground=BLUE2, activeforeground=WHITE,
                  relief="flat", padx=20, pady=6, cursor="hand2").pack(pady=10)

        # 比較結果テーブル
        res_wrap = tk.LabelFrame(self, text="比較結果", font=FONT_BOLD,
                                 bg=BG, fg=FG, padx=10, pady=8)
        res_wrap.pack(fill="x", padx=12)

        self.cmp_labels = {}
        header_row = tk.Frame(res_wrap, bg=BG)
        header_row.pack(fill="x")
        tk.Label(header_row, text="", width=22, bg=BG).pack(side="left")
        for i, name in enumerate(PLAN_NAMES):
            lbl = tk.Label(header_row, text=name, width=20, font=FONT_BOLD,
                           bg=BG, fg=PLAN_COLORS[i])
            lbl.pack(side="left")
            self.cmp_labels[f"hdr_{i}"] = lbl

        for key, label in [
            ("monthly",  "月返済額（円）"),
            ("total",    "総返済額（万円）"),
            ("interest", "利息総額（万円）"),
            ("ratio",    "利息割合（%）"),
        ]:
            row = tk.Frame(res_wrap, bg=BG)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label, width=22, anchor="w",
                     font=FONT, bg=BG, fg=FG2).pack(side="left")
            for i in range(4):
                lbl = tk.Label(row, text="---", width=20, font=FONT_BOLD,
                               bg=BG, fg=PLAN_COLORS[i], anchor="w")
                lbl.pack(side="left")
                self.cmp_labels[f"{key}_{i}"] = lbl

        # スケジュール比較テーブル（年次）
        sched_wrap = tk.LabelFrame(self, text="返済スケジュール比較（年次）",
                                   font=FONT_BOLD, bg=BG, fg=FG, padx=8, pady=8)
        sched_wrap.pack(fill="both", expand=True, padx=12, pady=(8, 4))

        # 動的に列を作る（後で更新）
        self.compare_tree_frame = sched_wrap
        self.compare_tree = None

        # 下ツールバー
        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", padx=12, pady=(0, 10))
        tk.Button(bar, text="CSVで保存", command=self._export_csv,
                  font=FONT, bg="#276749", fg=WHITE,
                  activebackground="#22543d", activeforeground=WHITE,
                  relief="flat", padx=14, pady=4, cursor="hand2").pack(side="right")

    def _flt(self, vd, key):
        val = vd[key].get().strip()
        if val == "":
            return None
        return float(val.replace(",", ""))

    def _compare(self):
        self._plans = []
        active_idx  = []

        for i, vd in enumerate(self.plan_vars):
            try:
                amount = self._flt(vd, "amount")
                rate   = self._flt(vd, "rate")
                years  = self._flt(vd, "years")
            except ValueError:
                messagebox.showerror("入力エラー", f"{PLAN_NAMES[i]} の入力値を確認してください。")
                return

            if amount is None or years is None:
                self._plans.append(None)
                continue
            if rate is None:
                rate = 0.0

            principal = amount * 10000
            months    = int(years * 12)
            pmt       = monthly_payment(principal, rate, months)
            sched     = amortization_schedule(principal, rate, months)
            total     = pmt * months
            total_int = total - principal
            ratio     = total_int / principal * 100 if principal else 0
            plan_name = vd["name"].get().strip() or PLAN_NAMES[i]

            self._plans.append({
                "name":      plan_name,
                "principal": principal,
                "rate":      rate,
                "months":    months,
                "monthly":   pmt,
                "total":     total,
                "interest":  total_int,
                "ratio":     ratio,
                "schedule":  sched,
            })
            active_idx.append(i)

        if not active_idx:
            messagebox.showwarning("比較", "少なくとも1プラン入力してください。")
            return

        # ヘッダー更新
        for i, vd in enumerate(self.plan_vars):
            name = vd["name"].get().strip() or PLAN_NAMES[i]
            self.cmp_labels[f"hdr_{i}"].config(text=name if self._plans[i] else "---")

        # 数値更新
        for key in ("monthly", "total", "interest", "ratio"):
            for i, plan in enumerate(self._plans):
                lbl = self.cmp_labels[f"{key}_{i}"]
                if plan is None:
                    lbl.config(text="---"); continue
                if key == "monthly":
                    lbl.config(text=f"{plan['monthly']:,.0f}")
                elif key in ("total", "interest"):
                    lbl.config(text=f"{plan[key]/10000:,.1f}")
                else:
                    lbl.config(text=f"{plan['ratio']:.1f}")

        # スケジュール比較ツリー再構築
        if self.compare_tree:
            self.compare_tree.destroy()

        active_plans = [(i, p) for i, p in enumerate(self._plans) if p is not None]
        n = len(active_plans)
        if n == 0:
            return

        cols   = ["年"]
        widths = [60]
        for i, plan in active_plans:
            cols   += [f"{plan['name']} 返済額", f"{plan['name']} 残高"]
            widths += [130, 130]

        frame = self.compare_tree_frame
        tree  = ttk.Treeview(frame, columns=cols, show="headings", height=12)
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="e" if col != "年" else "center")
        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        tree.tag_configure("odd",  background=STRIPE)
        tree.tag_configure("even", background=WHITE)
        self.compare_tree = tree

        # 最大年数
        max_yr = max(math.ceil(p["months"] / 12) for _, p in active_plans)
        for yr in range(1, max_yr + 1):
            row_vals = [f"{yr}年目"]
            for _, plan in active_plans:
                ys = yearly_summary(plan["schedule"])
                if yr in ys:
                    pay, _, _, bal = ys[yr]
                    row_vals += [f"{pay:,.0f}", f"{bal:,.0f}"]
                else:
                    row_vals += ["---", "---"]
            tag = "even" if yr % 2 == 0 else "odd"
            tree.insert("", "end", values=row_vals, tags=(tag,))

    def _export_csv(self):
        if not self._plans:
            messagebox.showwarning("CSV出力", "先に比較してください。"); return
        active_plans = [(i, p) for i, p in enumerate(self._plans) if p is not None]
        if not active_plans:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV ファイル", "*.csv"), ("すべてのファイル", "*.*")],
            initialfile="プラン比較.csv",
        )
        if not path:
            return

        max_yr = max(math.ceil(p["months"] / 12) for _, p in active_plans)
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            header = ["年"]
            for _, plan in active_plans:
                header += [f"{plan['name']} 返済額（円）", f"{plan['name']} 残高（円）"]
            writer.writerow(header)
            for yr in range(1, max_yr + 1):
                row = [f"{yr}年目"]
                for _, plan in active_plans:
                    ys = yearly_summary(plan["schedule"])
                    if yr in ys:
                        pay, _, _, bal = ys[yr]
                        row += [f"{pay:.0f}", f"{bal:.0f}"]
                    else:
                        row += ["", ""]
                writer.writerow(row)
        messagebox.showinfo("CSV出力完了", f"保存しました:\n{path}")


# ─────────────────────────────────────────
#  タブ3: グラフ（matplotlib が必要）
# ─────────────────────────────────────────

if HAS_MPL:
    class GraphTab(tk.Frame):
        def __init__(self, parent):
            super().__init__(parent, bg=BG)
            self._build()

        def _build(self):
            ctrl = tk.Frame(self, bg=BG)
            ctrl.pack(fill="x", padx=12, pady=(10, 4))

            tk.Label(ctrl, text="借入金額（万円）", font=FONT, bg=BG, fg=FG2).pack(side="left")
            self.v_amount = tk.StringVar(value="3000")
            tk.Entry(ctrl, textvariable=self.v_amount, width=8,
                     font=FONT, relief="solid", bd=1).pack(side="left", padx=(4, 12))

            tk.Label(ctrl, text="年利（%）", font=FONT, bg=BG, fg=FG2).pack(side="left")
            self.v_rate = tk.StringVar(value="1.5")
            tk.Entry(ctrl, textvariable=self.v_rate, width=6,
                     font=FONT, relief="solid", bd=1).pack(side="left", padx=(4, 12))

            tk.Label(ctrl, text="返済期間（年）", font=FONT, bg=BG, fg=FG2).pack(side="left")
            self.v_years = tk.StringVar(value="35")
            tk.Entry(ctrl, textvariable=self.v_years, width=6,
                     font=FONT, relief="solid", bd=1).pack(side="left", padx=(4, 12))

            tk.Button(ctrl, text="グラフ描画", command=self._draw,
                      font=FONT_BOLD, bg=BLUE, fg=WHITE,
                      activebackground=BLUE2, activeforeground=WHITE,
                      relief="flat", padx=16, pady=4, cursor="hand2").pack(side="left")

            self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(11, 4))
            self.fig.patch.set_facecolor(BG)
            self.canvas = FigureCanvasTkAgg(self.fig, master=self)
            self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=(0, 10))

        def _draw(self):
            try:
                amount = float(self.v_amount.get().replace(",", ""))
                rate   = float(self.v_rate.get().replace(",", ""))
                years  = float(self.v_years.get().replace(",", ""))
            except ValueError:
                messagebox.showerror("入力エラー", "数値を入力してください。"); return

            principal = amount * 10000
            months    = int(years * 12)
            sched     = amortization_schedule(principal, rate, months)
            ys        = yearly_summary(sched)

            yrs      = list(ys.keys())
            balances = [v[3] / 10000 for v in ys.values()]
            prins    = [v[1] / 10000 for v in ys.values()]
            intrs    = [v[2] / 10000 for v in ys.values()]

            for ax in (self.ax1, self.ax2):
                ax.clear()
                ax.set_facecolor(WHITE)

            # 残高推移
            self.ax1.plot(yrs, balances, color=BLUE, linewidth=2, marker="o", markersize=3)
            self.ax1.fill_between(yrs, balances, alpha=0.15, color=BLUE)
            self.ax1.set_title("残高推移（万円）", fontsize=11)
            self.ax1.set_xlabel("返済年数")
            self.ax1.set_ylabel("残高（万円）")
            self.ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
            self.ax1.grid(True, linestyle="--", alpha=0.5)

            # 元本・利息の積み上げ棒グラフ
            self.ax2.bar(yrs, prins, label="元本", color=BLUE,   alpha=0.85)
            self.ax2.bar(yrs, intrs, bottom=prins, label="利息", color="#fc8181", alpha=0.85)
            self.ax2.set_title("年間返済内訳（万円）", fontsize=11)
            self.ax2.set_xlabel("返済年数")
            self.ax2.set_ylabel("金額（万円）")
            self.ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.1f}"))
            self.ax2.legend()
            self.ax2.grid(True, axis="y", linestyle="--", alpha=0.5)

            self.fig.tight_layout()
            self.canvas.draw()


# ─────────────────────────────────────────
#  エントリーポイント
# ─────────────────────────────────────────

def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
