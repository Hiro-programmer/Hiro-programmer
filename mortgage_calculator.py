"""
住宅ローン計算アプリ (Mortgage Calculator) - デザイン強化版
Windows用 Python/tkinter + ttkbootstrap アプリケーション

機能:
  - 元利均等 / 元金均等 返済の計算
  - 返済スケジュール（月次/年次）
  - CSV出力
  - 複数プラン比較（最大4プラン）
  - 残高推移グラフ（matplotlib）
"""

import csv
import math
import tkinter as tk
from tkinter import messagebox, filedialog

try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    HAS_TTK = True
except ImportError:
    import tkinter.ttk as ttk
    HAS_TTK = False

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.ticker as mticker
    matplotlib.rcParams["font.family"] = ["Yu Gothic", "Meiryo", "MS Gothic", "sans-serif"]
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

# ─────────────────────────────────────────
#  カラーテーマ
# ─────────────────────────────────────────
C = {
    "primary":    "#1a56db",
    "primary_dk": "#1e429f",
    "success":    "#057a55",
    "danger":     "#c81e1e",
    "warn":       "#9f580a",
    "bg":         "#f9fafb",
    "card":       "#ffffff",
    "border":     "#e5e7eb",
    "text":       "#111827",
    "muted":      "#6b7280",
    "stripe":     "#f3f4f6",
    "accent":     "#eff6ff",
    "plan": ["#1a56db", "#057a55", "#c81e1e", "#7e3af2"],
}

FONT      = ("Yu Gothic UI", 10)
FONT_B    = ("Yu Gothic UI", 10, "bold")
FONT_SM   = ("Yu Gothic UI", 9)
FONT_LG   = ("Yu Gothic UI", 13, "bold")
FONT_XL   = ("Yu Gothic UI", 17, "bold")

# ─────────────────────────────────────────
#  計算ロジック
# ─────────────────────────────────────────

def calc_monthly(principal, annual_rate, months):
    if annual_rate == 0:
        return principal / months
    r = annual_rate / 100 / 12
    return principal * r * (1 + r) ** months / ((1 + r) ** months - 1)


def amortization(principal, annual_rate, months, method="equal_payment"):
    """
    method: "equal_payment"  = 元利均等
            "equal_principal" = 元金均等
    """
    schedule = []
    balance = principal
    r = annual_rate / 100 / 12

    if method == "equal_payment":
        pmt = calc_monthly(principal, annual_rate, months)
        for m in range(1, months + 1):
            interest = balance * r if annual_rate != 0 else 0.0
            prin = pmt - interest
            balance = max(balance - prin, 0.0)
            schedule.append((m, pmt, prin, interest, balance))

    else:  # equal_principal
        prin_fixed = principal / months
        for m in range(1, months + 1):
            interest = balance * r if annual_rate != 0 else 0.0
            pmt = prin_fixed + interest
            balance = max(balance - prin_fixed, 0.0)
            schedule.append((m, pmt, prin_fixed, interest, balance))

    return schedule


def yearly(schedule):
    ys = {}
    for m, pmt, prin, intr, bal in schedule:
        yr = math.ceil(m / 12)
        if yr not in ys:
            ys[yr] = [0.0, 0.0, 0.0, bal]
        ys[yr][0] += pmt
        ys[yr][1] += prin
        ys[yr][2] += intr
        ys[yr][3] = bal
    return ys


# ─────────────────────────────────────────
#  共通ウィジェット
# ─────────────────────────────────────────

def card(parent, title=None, **pack_kw):
    outer = tk.Frame(parent, bg=C["border"], bd=0)
    outer.pack(**pack_kw)
    inner = tk.Frame(outer, bg=C["card"], padx=16, pady=12)
    inner.pack(fill="both", expand=True, padx=1, pady=1)
    if title:
        tk.Label(inner, text=title, font=FONT_LG,
                 bg=C["card"], fg=C["primary"]).pack(anchor="w", pady=(0, 8))
    return inner


def field_row(parent, label, var, width=12, hint=""):
    row = tk.Frame(parent, bg=C["card"])
    row.pack(fill="x", pady=4)
    lf = tk.Frame(row, bg=C["card"])
    lf.pack(side="left", fill="x", expand=True)
    tk.Label(lf, text=label, font=FONT_B,
             bg=C["card"], fg=C["text"]).pack(anchor="w")
    if hint:
        tk.Label(lf, text=hint, font=FONT_SM,
                 bg=C["card"], fg=C["muted"]).pack(anchor="w")
    e = tk.Entry(row, textvariable=var, width=width, font=FONT,
                 relief="solid", bd=1, highlightthickness=1,
                 highlightcolor=C["primary"], highlightbackground=C["border"])
    e.pack(side="right", padx=(8, 0))
    return e


def styled_btn(parent, text, cmd, color=None, **kw):
    color = color or C["primary"]
    b = tk.Button(parent, text=text, command=cmd, font=FONT_B,
                  bg=color, fg="white", activebackground=C["primary_dk"],
                  activeforeground="white", relief="flat",
                  cursor="hand2", bd=0, **kw)
    b.bind("<Enter>", lambda e: b.config(bg=C["primary_dk"]))
    b.bind("<Leave>", lambda e: b.config(bg=color))
    return b


def result_kv(parent, label, key_dict, key):
    row = tk.Frame(parent, bg=C["accent"], pady=6)
    row.pack(fill="x", pady=2)
    tk.Frame(row, bg=C["primary"], width=4).pack(side="left", fill="y", padx=(0, 10))
    tk.Label(row, text=label, font=FONT, bg=C["accent"],
             fg=C["muted"], width=18, anchor="w").pack(side="left")
    lbl = tk.Label(row, text="---", font=FONT_B,
                   bg=C["accent"], fg=C["primary"], anchor="w")
    lbl.pack(side="left")
    key_dict[key] = lbl
    return lbl


def make_tree(parent, cols, widths, height=13):
    style = ttk.Style() if not HAS_TTK else None
    frame = tk.Frame(parent, bg=C["bg"])
    frame.pack(fill="both", expand=True)
    tree = ttk.Treeview(frame, columns=cols, show="headings", height=height)
    for col, w in zip(cols, widths):
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor="e" if col != cols[0] else "center",
                    minwidth=40)
    sb_y = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    sb_x = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
    tree.grid(row=0, column=0, sticky="nsew")
    sb_y.grid(row=0, column=1, sticky="ns")
    sb_x.grid(row=1, column=0, sticky="ew")
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    tree.tag_configure("odd",  background=C["stripe"])
    tree.tag_configure("even", background=C["card"])
    return tree


# ─────────────────────────────────────────
#  メインアプリ
# ─────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("住宅ローン計算アプリ")
        self.configure(bg=C["bg"])
        self.minsize(900, 680)
        self.resizable(True, True)
        self._build()

    def _build(self):
        # ヘッダー
        hdr = tk.Frame(self, bg=C["primary"], pady=0)
        hdr.pack(fill="x")
        inner_hdr = tk.Frame(hdr, bg=C["primary"])
        inner_hdr.pack(fill="x", padx=24, pady=14)
        tk.Label(inner_hdr, text="🏠  住宅ローン計算アプリ",
                 font=FONT_XL, bg=C["primary"], fg="white").pack(side="left")
        tk.Label(inner_hdr, text="Mortgage Calculator",
                 font=FONT_SM, bg=C["primary"], fg="#93c5fd").pack(side="left", padx=(12, 0), pady=(4, 0))

        # タブ
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=16, pady=12)

        self.t_calc    = CalcTab(nb)
        self.t_compare = CompareTab(nb)
        if HAS_MPL:
            self.t_graph = GraphTab(nb)

        nb.add(self.t_calc,    text="  📊 計算・スケジュール  ")
        nb.add(self.t_compare, text="  🔀 複数プラン比較  ")
        if HAS_MPL:
            nb.add(self.t_graph, text="  📈 グラフ  ")


# ─────────────────────────────────────────
#  タブ1: 計算 + スケジュール
# ─────────────────────────────────────────

class CalcTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=C["bg"])
        self._sched = []
        self._build()

    def _build(self):
        # 上段: 入力 + 結果 横並び
        top = tk.Frame(self, bg=C["bg"])
        top.pack(fill="x", padx=4, pady=(8, 0))

        # ── 入力カード ──
        inp = card(top, "ローン条件の入力",
                   side="left", fill="both", expand=True, padx=(0, 8), pady=0)

        self.v = {k: tk.StringVar(value=d) for k, d in [
            ("amount",  "3000"),
            ("rate",    "1.5"),
            ("years",   "35"),
            ("b_count", "0"),
            ("b_amt",   "0"),
        ]}
        field_row(inp, "借入金額",     self.v["amount"], hint="単位: 万円")
        field_row(inp, "年利",         self.v["rate"],   hint="単位: %（例: 1.5）")
        field_row(inp, "返済期間",     self.v["years"],  hint="単位: 年")
        field_row(inp, "ボーナス返済回数", self.v["b_count"], hint="年何回（0=なし）")
        field_row(inp, "ボーナス返済額",   self.v["b_amt"],   hint="単位: 万円/回")

        # 返済方式
        method_row = tk.Frame(inp, bg=C["card"])
        method_row.pack(fill="x", pady=(8, 0))
        tk.Label(method_row, text="返済方式", font=FONT_B,
                 bg=C["card"], fg=C["text"]).pack(anchor="w")
        self.method_var = tk.StringVar(value="equal_payment")
        for val, lbl in [("equal_payment", "元利均等"), ("equal_principal", "元金均等")]:
            tk.Radiobutton(method_row, text=lbl, variable=self.method_var, value=val,
                           font=FONT, bg=C["card"], fg=C["text"],
                           activebackground=C["card"]).pack(side="left", padx=(0, 16))

        tk.Frame(inp, bg=C["border"], height=1).pack(fill="x", pady=10)
        styled_btn(inp, "  計算する  ", self._calc, padx=10, pady=8).pack(anchor="e")

        # ── 結果カード ──
        res = card(top, "計算結果",
                   side="left", fill="both", expand=True, padx=(0, 0), pady=0)
        self.rl = {}
        result_kv(res, "月返済額",         self.rl, "monthly")
        result_kv(res, "総返済額",         self.rl, "total")
        result_kv(res, "うち利息総額",     self.rl, "interest")
        result_kv(res, "利息割合",         self.rl, "ratio")

        # ── スケジュール ──
        sched_card = card(self, "返済スケジュール",
                          fill="both", expand=True, padx=4, pady=(8, 4))

        cols   = ("月", "返済額（円）", "元本（円）", "利息（円）", "残高（円）")
        widths = [60, 130, 120, 110, 140]
        self.tree = make_tree(sched_card, cols, widths)

        # ツールバー
        bar = tk.Frame(self, bg=C["bg"])
        bar.pack(fill="x", padx=4, pady=(0, 8))

        self.yearly_var = tk.BooleanVar(value=False)
        tk.Checkbutton(bar, text="年単位で表示", variable=self.yearly_var,
                       command=self._refresh, font=FONT,
                       bg=C["bg"], fg=C["muted"]).pack(side="left")

        styled_btn(bar, "  💾 CSVで保存  ", self._csv,
                   color=C["success"], padx=10, pady=5).pack(side="right")

    def _flt(self, key):
        try:
            return float(self.v[key].get().replace(",", ""))
        except ValueError:
            raise ValueError(f"「{key}」の値が正しくありません。")

    def _calc(self):
        try:
            p_man  = self._flt("amount")
            rate   = self._flt("rate")
            years  = self._flt("years")
            b_cnt  = int(self._flt("b_count"))
            b_man  = self._flt("b_amt")
            if p_man <= 0: raise ValueError("借入金額は0より大きい値を入力してください。")
            if rate  < 0:  raise ValueError("年利は0以上の値を入力してください。")
            if years <= 0: raise ValueError("返済期間は0より大きい値を入力してください。")
        except ValueError as e:
            messagebox.showerror("入力エラー", str(e)); return

        principal = p_man * 10000
        months    = int(years * 12)
        method    = self.method_var.get()
        self._sched = amortization(principal, rate, months, method)

        first_pmt   = self._sched[0][1]
        bonus_total = b_man * 10000 * b_cnt * years
        total       = sum(row[1] for row in self._sched) + bonus_total
        total_int   = total - principal
        ratio       = total_int / principal * 100 if principal else 0

        method_lbl = "（元利均等）" if method == "equal_payment" else "（元金均等・初月）"
        self.rl["monthly"].config( text=f"{first_pmt:,.0f} 円 {method_lbl}")
        self.rl["total"].config(   text=f"{total:,.0f} 円  ({total/10000:,.1f} 万円)")
        self.rl["interest"].config(text=f"{total_int:,.0f} 円  ({total_int/10000:,.1f} 万円)")
        self.rl["ratio"].config(   text=f"{ratio:.1f} %")
        self._refresh()

    def _refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        if not self._sched:
            return
        if self.yearly_var.get():
            for i, (yr, (pay, prin, intr, bal)) in enumerate(yearly(self._sched).items()):
                self.tree.insert("", "end",
                    values=(f"{yr}年目", f"{pay:,.0f}", f"{prin:,.0f}", f"{intr:,.0f}", f"{bal:,.0f}"),
                    tags=("even" if i % 2 == 0 else "odd",))
        else:
            for i, (m, pmt, prin, intr, bal) in enumerate(self._sched):
                self.tree.insert("", "end",
                    values=(m, f"{pmt:,.0f}", f"{prin:,.0f}", f"{intr:,.0f}", f"{bal:,.0f}"),
                    tags=("even" if i % 2 == 0 else "odd",))

    def _csv(self):
        if not self._sched:
            messagebox.showwarning("CSV出力", "先に計算してください。"); return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("すべて", "*.*")],
            initialfile="返済スケジュール.csv")
        if not path: return
        rows = yearly(self._sched).items() if self.yearly_var.get() else None
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            if self.yearly_var.get():
                w.writerow(["年", "返済額合計（円）", "元本合計（円）", "利息合計（円）", "残高（円）"])
                for yr, (pay, prin, intr, bal) in yearly(self._sched).items():
                    w.writerow([f"{yr}年目", f"{pay:.0f}", f"{prin:.0f}", f"{intr:.0f}", f"{bal:.0f}"])
            else:
                w.writerow(["月", "返済額（円）", "元本（円）", "利息（円）", "残高（円）"])
                for m, pmt, prin, intr, bal in self._sched:
                    w.writerow([m, f"{pmt:.0f}", f"{prin:.0f}", f"{intr:.0f}", f"{bal:.0f}"])
        messagebox.showinfo("CSV出力完了", f"保存しました:\n{path}")


# ─────────────────────────────────────────
#  タブ2: 複数プラン比較
# ─────────────────────────────────────────

PLAN_LABELS = ["プランA", "プランB", "プランC", "プランD"]

class CompareTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=C["bg"])
        self._plans = []
        self._build()

    def _build(self):
        tk.Label(self, text="最大4プランの条件を入力して比較できます（空欄のプランは無視されます）",
                 font=FONT_SM, bg=C["bg"], fg=C["muted"]).pack(anchor="w", padx=8, pady=(8, 4))

        # プラン入力（横並び）
        plan_row = tk.Frame(self, bg=C["bg"])
        plan_row.pack(fill="x", padx=4)

        self.pv = []
        for i in range(4):
            pf = tk.Frame(plan_row, bg=C["card"],
                          highlightthickness=2,
                          highlightbackground=C["plan"][i])
            pf.pack(side="left", fill="both", expand=True,
                    padx=(0, 6 if i < 3 else 0))
            hdr = tk.Frame(pf, bg=C["plan"][i], pady=5)
            hdr.pack(fill="x")
            tk.Label(hdr, text=PLAN_LABELS[i], font=FONT_B,
                     bg=C["plan"][i], fg="white").pack()

            body = tk.Frame(pf, bg=C["card"], padx=10, pady=8)
            body.pack(fill="x")
            vd = {}
            for label, key, default in [
                ("借入金額（万円）", "amount", "3000" if i == 0 else ""),
                ("年利（%）",       "rate",   "1.5"  if i == 0 else ""),
                ("返済期間（年）",   "years",  "35"   if i == 0 else ""),
                ("プラン名",        "name",   ""),
            ]:
                vd[key] = tk.StringVar(value=default)
                r = tk.Frame(body, bg=C["card"])
                r.pack(fill="x", pady=2)
                tk.Label(r, text=label, font=FONT_SM,
                         bg=C["card"], fg=C["muted"], anchor="w").pack(anchor="w")
                tk.Entry(r, textvariable=vd[key], font=FONT,
                         relief="solid", bd=1).pack(fill="x")
            self.pv.append(vd)

        # 比較ボタン
        btn_row = tk.Frame(self, bg=C["bg"])
        btn_row.pack(fill="x", padx=4, pady=8)
        styled_btn(btn_row, "  🔀 比較する  ", self._compare,
                   padx=14, pady=7).pack(side="left")
        styled_btn(btn_row, "  💾 CSVで保存  ", self._csv,
                   color=C["success"], padx=14, pady=7).pack(side="left", padx=(8, 0))

        # サマリーテーブル
        sum_card = card(self, "比較サマリー",
                        fill="x", padx=4, pady=(0, 6))
        self.cl = {}
        hrow = tk.Frame(sum_card, bg=C["card"])
        hrow.pack(fill="x")
        tk.Label(hrow, text="", width=20, bg=C["card"]).pack(side="left")
        for i in range(4):
            lbl = tk.Label(hrow, text=PLAN_LABELS[i], width=18,
                           font=FONT_B, bg=C["card"], fg=C["plan"][i])
            lbl.pack(side="left")
            self.cl[f"h{i}"] = lbl

        for key, label in [
            ("monthly",  "月返済額（円）"),
            ("total",    "総返済額（万円）"),
            ("interest", "利息総額（万円）"),
            ("ratio",    "利息割合（%）"),
        ]:
            row = tk.Frame(sum_card, bg=C["stripe"])
            row.pack(fill="x", pady=1)
            tk.Label(row, text=label, width=20, anchor="w",
                     font=FONT, bg=C["stripe"], fg=C["muted"]).pack(side="left")
            for i in range(4):
                lbl = tk.Label(row, text="---", width=18, font=FONT_B,
                               bg=C["stripe"], fg=C["plan"][i], anchor="w")
                lbl.pack(side="left")
                self.cl[f"{key}_{i}"] = lbl

        # 詳細スケジュール
        det_card = card(self, "年次スケジュール比較",
                        fill="both", expand=True, padx=4, pady=(0, 4))
        self._tree_frame = det_card
        self._tree = None

    def _flt(self, vd, key):
        v = vd[key].get().strip()
        return None if v == "" else float(v.replace(",", ""))

    def _compare(self):
        self._plans = []
        for i, vd in enumerate(self.pv):
            try:
                amt  = self._flt(vd, "amount")
                rate = self._flt(vd, "rate")
                yrs  = self._flt(vd, "years")
            except ValueError:
                messagebox.showerror("入力エラー", f"{PLAN_LABELS[i]} の値を確認してください。")
                return
            if amt is None or yrs is None:
                self._plans.append(None); continue
            rate = rate or 0.0
            p = amt * 10000
            m = int(yrs * 12)
            sc = amortization(p, rate, m)
            total    = sum(r[1] for r in sc)
            total_i  = total - p
            name     = vd["name"].get().strip() or PLAN_LABELS[i]
            self._plans.append(dict(
                name=name, principal=p, rate=rate, months=m,
                monthly=sc[0][1], total=total,
                interest=total_i, ratio=total_i/p*100 if p else 0,
                schedule=sc))
            self.cl[f"h{i}"].config(text=name)

        active = [(i, p) for i, p in enumerate(self._plans) if p]
        if not active:
            messagebox.showwarning("比較", "少なくとも1プラン入力してください。"); return

        for key in ("monthly", "total", "interest", "ratio"):
            for i, plan in enumerate(self._plans):
                lbl = self.cl[f"{key}_{i}"]
                if not plan:
                    lbl.config(text="---"); continue
                if key == "monthly":
                    lbl.config(text=f"{plan['monthly']:,.0f}")
                elif key in ("total", "interest"):
                    lbl.config(text=f"{plan[key]/10000:,.1f}")
                else:
                    lbl.config(text=f"{plan['ratio']:.1f}")

        # ツリー再構築
        if self._tree:
            self._tree.master.destroy()
            self._tree = None

        cols   = ["年"]
        widths = [65]
        for i, p in active:
            cols   += [f"{p['name']} 返済額", f"{p['name']} 残高"]
            widths += [140, 140]

        self._tree = make_tree(self._tree_frame, cols, widths, height=11)
        max_yr = max(math.ceil(p["months"] / 12) for _, p in active)
        for yr in range(1, max_yr + 1):
            row = [f"{yr}年目"]
            for i, p in active:
                ys = yearly(p["schedule"])
                if yr in ys:
                    row += [f"{ys[yr][0]:,.0f}", f"{ys[yr][3]:,.0f}"]
                else:
                    row += ["---", "---"]
            self._tree.insert("", "end", values=row,
                              tags=("even" if yr % 2 == 0 else "odd",))

    def _csv(self):
        active = [(i, p) for i, p in enumerate(self._plans) if p]
        if not active:
            messagebox.showwarning("CSV出力", "先に比較してください。"); return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("すべて", "*.*")],
            initialfile="プラン比較.csv")
        if not path: return
        max_yr = max(math.ceil(p["months"] / 12) for _, p in active)
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            hdr = ["年"]
            for _, p in active:
                hdr += [f"{p['name']} 返済額（円）", f"{p['name']} 残高（円）"]
            w.writerow(hdr)
            for yr in range(1, max_yr + 1):
                row = [f"{yr}年目"]
                for _, p in active:
                    ys = yearly(p["schedule"])
                    row += ([f"{ys[yr][0]:.0f}", f"{ys[yr][3]:.0f}"] if yr in ys else ["", ""])
                w.writerow(row)
        messagebox.showinfo("CSV出力完了", f"保存しました:\n{path}")


# ─────────────────────────────────────────
#  タブ3: グラフ
# ─────────────────────────────────────────

if HAS_MPL:
    class GraphTab(tk.Frame):
        def __init__(self, parent):
            super().__init__(parent, bg=C["bg"])
            self._build()

        def _build(self):
            ctrl = card(self, fill="x", padx=4, pady=(8, 4))

            row1 = tk.Frame(ctrl, bg=C["card"])
            row1.pack(fill="x")
            for label, key, default in [
                ("借入金額（万円）", "amount", "3000"),
                ("年利（%）",        "rate",   "1.5"),
                ("返済期間（年）",    "years",  "35"),
            ]:
                f = tk.Frame(row1, bg=C["card"])
                f.pack(side="left", padx=(0, 16))
                tk.Label(f, text=label, font=FONT_B,
                         bg=C["card"], fg=C["text"]).pack(anchor="w")
                setattr(self, f"v_{key}", tk.StringVar(value=default))
                tk.Entry(f, textvariable=getattr(self, f"v_{key}"),
                         width=10, font=FONT, relief="solid", bd=1).pack()

            # 方式選択
            f = tk.Frame(row1, bg=C["card"])
            f.pack(side="left", padx=(0, 16))
            tk.Label(f, text="返済方式", font=FONT_B,
                     bg=C["card"], fg=C["text"]).pack(anchor="w")
            self.v_method = tk.StringVar(value="equal_payment")
            for val, lbl in [("equal_payment", "元利均等"), ("equal_principal", "元金均等")]:
                tk.Radiobutton(f, text=lbl, variable=self.v_method, value=val,
                               font=FONT_SM, bg=C["card"]).pack(anchor="w")

            styled_btn(row1, "  📈 グラフ描画  ", self._draw,
                       padx=12, pady=6).pack(side="left", pady=(12, 0))

            # グラフキャンバス
            self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
            self.fig.patch.set_facecolor(C["bg"])
            self.canvas = FigureCanvasTkAgg(self.fig, master=self)
            self.canvas.get_tk_widget().pack(fill="both", expand=True,
                                             padx=8, pady=(0, 8))

        def _draw(self):
            try:
                amount = float(self.v_amount.get().replace(",", ""))
                rate   = float(self.v_rate.get().replace(",", ""))
                years  = float(self.v_years.get().replace(",", ""))
            except ValueError:
                messagebox.showerror("入力エラー", "数値を入力してください。"); return

            principal = amount * 10000
            months    = int(years * 12)
            method    = self.v_method.get()
            sched     = amortization(principal, rate, months, method)
            ys        = yearly(sched)

            yrs  = list(ys.keys())
            bals = [v[3] / 10000 for v in ys.values()]
            prns = [v[1] / 10000 for v in ys.values()]
            ints = [v[2] / 10000 for v in ys.values()]

            for ax in (self.ax1, self.ax2):
                ax.clear()
                ax.set_facecolor(C["card"])
                for spine in ax.spines.values():
                    spine.set_color(C["border"])

            # 残高推移
            self.ax1.plot(yrs, bals, color=C["primary"], lw=2.5,
                          marker="o", markersize=3, label="残高")
            self.ax1.fill_between(yrs, bals, alpha=0.12, color=C["primary"])
            self.ax1.set_title("残高推移", fontsize=12, pad=8, color=C["text"])
            self.ax1.set_xlabel("返済年数", color=C["muted"])
            self.ax1.set_ylabel("残高（万円）", color=C["muted"])
            self.ax1.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
            self.ax1.grid(True, linestyle="--", alpha=0.4, color=C["border"])
            self.ax1.tick_params(colors=C["muted"])

            # 年間内訳
            self.ax2.bar(yrs, prns, label="元本",
                         color=C["primary"], alpha=0.85, width=0.8)
            self.ax2.bar(yrs, ints, bottom=prns, label="利息",
                         color="#f87171", alpha=0.85, width=0.8)
            self.ax2.set_title("年間返済内訳（元本 vs 利息）",
                               fontsize=12, pad=8, color=C["text"])
            self.ax2.set_xlabel("返済年数", color=C["muted"])
            self.ax2.set_ylabel("金額（万円）", color=C["muted"])
            self.ax2.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda x, _: f"{x:,.1f}"))
            self.ax2.legend(facecolor=C["card"], edgecolor=C["border"])
            self.ax2.grid(True, axis="y", linestyle="--",
                          alpha=0.4, color=C["border"])
            self.ax2.tick_params(colors=C["muted"])

            method_lbl = "元利均等" if method == "equal_payment" else "元金均等"
            self.fig.suptitle(
                f"{amount:,.0f}万円  年利{rate}%  {int(years)}年  {method_lbl}",
                fontsize=10, color=C["muted"])
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
