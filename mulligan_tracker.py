import csv
import ctypes
import json
import os
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


APP_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "ShadowverseMulliganTracker"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE = DATA_DIR / "mulligan_data.json"


def enable_windows_dpi_awareness():
    """Ask Windows to render the app at the monitor's native DPI."""
    if os.name != "nt":
        return
    try:
        # PROCESS_PER_MONITOR_DPI_AWARE_V2; must be set before creating Tk windows.
        if ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
            return
    except (AttributeError, OSError):
        pass
    try:
        # Fallback for Windows versions without the per-monitor v2 API.
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except (AttributeError, OSError):
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        pass


def load_data():
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return {"cards": data.get("cards", []), "matches": data.get("matches", []), "templates": data.get("templates", {})}
    except (OSError, json.JSONDecodeError):
        return {"cards": [], "matches": [], "templates": {}}


class Tracker(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("シャドウバース WB マリガントラッカー")
        self.geometry("1180x800")
        self.minsize(960, 680)
        icon_path = Path(getattr(sys, "_MEIPASS", APP_DIR)) / "mulligan_tracker.ico"
        if icon_path.exists():
            try: self.iconbitmap(default=str(icon_path))
            except tk.TclError: pass
        self.data = load_data()
        self.card_vars = []
        self.exchange_vars = []
        self.redraw_vars = []
        self.build_ui()
        self.refresh_cards()
        self.refresh_history()
        self.refresh_stats()

    def save(self):
        DATA_FILE.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")

    def build_ui(self):
        style = ttk.Style(self)
        try: style.theme_use("clam")
        except tk.TclError: pass
        self.configure(background="#f4f1f8")
        style.configure("TFrame", background="#f4f1f8")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("TLabel", background="#f4f1f8", foreground="#292335", font=("Yu Gothic UI", 10))
        style.configure("Title.TLabel", font=("Yu Gothic UI", 22, "bold"), foreground="#ffffff", background="#302238")
        style.configure("Subtitle.TLabel", font=("Yu Gothic UI", 10), foreground="#eaddeb", background="#302238")
        style.configure("Section.TLabel", font=("Yu Gothic UI", 14, "bold"), foreground="#302238", background="#ffffff")
        style.configure("Hint.TLabel", foreground="#716b79", font=("Yu Gothic UI", 9))
        style.configure("Card.TLabel", background="#ffffff")
        style.configure("Card.Hint.TLabel", background="#ffffff", foreground="#716b79", font=("Yu Gothic UI", 9))
        style.configure("TNotebook", background="#f4f1f8", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(18, 10), font=("Yu Gothic UI", 10, "bold"), background="#e8e1ed", foreground="#51475a")
        style.map("TNotebook.Tab", background=[("selected", "#ffffff")], foreground=[("selected", "#a33475")])
        style.configure("TButton", padding=(12, 8), font=("Yu Gothic UI", 10))
        style.configure("Accent.TButton", background="#a33475", foreground="#ffffff", padding=(16, 10), font=("Yu Gothic UI", 10, "bold"))
        style.map("Accent.TButton", background=[("active", "#84275f"), ("disabled", "#cdb8c6")])
        style.configure("Treeview", rowheight=30, font=("Yu Gothic UI", 10), background="#ffffff", fieldbackground="#ffffff")
        style.configure("Treeview.Heading", font=("Yu Gothic UI", 10, "bold"), background="#e9e2ee", foreground="#302238", padding=(8, 8))
        root = ttk.Frame(self, padding=(18, 14))
        root.pack(fill="both", expand=True)
        header = tk.Frame(root, bg="#302238", padx=20, pady=16)
        header.pack(fill="x", pady=(0, 14))
        ttk.Label(header, text="マリガントラッカー", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="初手とマリガンを記録して、カードごとの傾向をチェック", style="Subtitle.TLabel").pack(anchor="w", pady=(4, 0))
        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True)
        self.record_tab = ttk.Frame(self.tabs, padding=14)
        self.stats_tab = ttk.Frame(self.tabs, padding=14)
        self.history_tab = ttk.Frame(self.tabs, padding=14)
        self.cards_tab = ttk.Frame(self.tabs, padding=14)
        self.tabs.add(self.record_tab, text="対戦を記録")
        self.tabs.add(self.stats_tab, text="カード別統計")
        self.tabs.add(self.history_tab, text="対戦履歴")
        self.tabs.add(self.cards_tab, text="カード登録")
        self.build_record()
        self.build_stats()
        self.build_history()
        self.build_cards()

    def build_record(self):
        f = self.record_tab
        row = ttk.Frame(f, style="Card.TFrame", padding=14); row.pack(fill="x", pady=(0, 14))
        ttk.Label(row, text="デッキ名", style="Card.TLabel").pack(side="left")
        self.deck_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.deck_var, width=34).pack(side="left", padx=(8, 24), ipady=4)
        ttk.Label(row, text="手番", style="Card.TLabel").pack(side="left")
        self.turn_var = tk.StringVar(value="先攻")
        ttk.Combobox(row, textvariable=self.turn_var, values=["先攻", "後攻"], state="readonly", width=9).pack(side="left", padx=8)
        hand = ttk.Frame(f, style="Card.TFrame", padding=16); hand.pack(fill="x", pady=(0, 12))
        ttk.Label(hand, text="1　初期手札", style="Section.TLabel").pack(anchor="w", pady=(0, 8))
        ttk.Button(hand, text="画面から4枚を読み取る", style="Accent.TButton", command=self.capture_initial).pack(anchor="w", pady=(0, 10))
        self.initial_frame = ttk.Frame(hand, style="Card.TFrame"); self.initial_frame.pack(anchor="w")
        ttk.Label(hand, text="交換するカードを選んでね", style="Card.Hint.TLabel").pack(anchor="w", pady=(12, 5))
        self.exchange_frame = ttk.Frame(hand, style="Card.TFrame"); self.exchange_frame.pack(anchor="w")
        redraw = ttk.Frame(f, style="Card.TFrame", padding=16); redraw.pack(fill="x", pady=(0, 12))
        ttk.Label(redraw, text="2　引き直し後", style="Section.TLabel").pack(anchor="w", pady=(0, 8))
        ttk.Label(redraw, text="交換した枚数分のカードを記録", style="Card.Hint.TLabel").pack(anchor="w", pady=(0, 6))
        self.redraw_frame = ttk.Frame(redraw, style="Card.TFrame"); self.redraw_frame.pack(anchor="w")
        self.redraw_note = ttk.Label(redraw, text="先に初期手札を選ぶと、交換欄が使えるよ。", style="Card.Hint.TLabel")
        self.redraw_note.pack(anchor="w", pady=(8, 8))
        self.capture_redraw_button = ttk.Button(redraw, text="画面から引き直し後を読み取る", command=self.capture_final)
        self.capture_redraw_button.pack(anchor="w", pady=(0, 6))
        ttk.Label(redraw, text="見本画像と照合するよ。候補は保存前に確認・修正できるよ。", style="Card.Hint.TLabel").pack(anchor="w")
        ttk.Button(f, text="この対戦を保存", style="Accent.TButton", command=self.save_match).pack(anchor="e", pady=(2, 8))
        self.make_hand_controls()

    def make_hand_controls(self):
        self.card_vars, self.exchange_vars, self.redraw_vars = [], [], []
        for child in self.initial_frame.winfo_children() + self.exchange_frame.winfo_children() + self.redraw_frame.winfo_children():
            child.destroy()
        self.initial_boxes = []
        for i in range(4):
            v = tk.StringVar()
            box = ttk.Combobox(self.initial_frame, textvariable=v, state="normal", width=24)
            box.grid(row=0, column=i, padx=(0, 8), pady=2)
            box.bind("<<ComboboxSelected>>", lambda _e: self.update_exchange_ui())
            self.card_vars.append(v); self.initial_boxes.append(box)
        for i in range(4):
            v = tk.BooleanVar(value=False)
            cb = ttk.Checkbutton(self.exchange_frame, text=f"{i+1}枚目を交換", variable=v, command=self.update_exchange_ui)
            cb.grid(row=0, column=i, sticky="w", padx=(0, 14))
            self.exchange_vars.append(v)

    def update_exchange_ui(self):
        for child in self.redraw_frame.winfo_children(): child.destroy()
        self.redraw_vars = []
        count = sum(v.get() for v in self.exchange_vars)
        names = [v.get() for v in self.card_vars]
        for i, var in enumerate(self.exchange_vars):
            cb = self.exchange_frame.winfo_children()[i]
            cb.configure(text=f"{i+1}枚目: {names[i] or '未選択'} を交換")
            cb.configure(state="normal" if names[i] else "disabled")
            if not names[i]: var.set(False)
        for i in range(count):
            v = tk.StringVar()
            box = ttk.Combobox(self.redraw_frame, textvariable=v, values=self.card_names(), state="normal", width=24)
            box.grid(row=0, column=i, padx=(0, 8), pady=2)
            self.redraw_vars.append(v)
        self.redraw_note.configure(text=f"交換枚数: {count}枚" if count else "交換なしで保存すると、初期手札をそのまま記録するよ。")

    def build_stats(self):
        bar = ttk.Frame(self.stats_tab); bar.pack(fill="x", pady=(0, 8))
        ttk.Label(bar, text="集計対象デッキ").pack(side="left")
        self.stats_deck = tk.StringVar(value="すべて")
        self.stats_filter = ttk.Combobox(bar, textvariable=self.stats_deck, state="readonly", width=28)
        self.stats_filter.pack(side="left", padx=8)
        self.stats_filter.bind("<<ComboboxSelected>>", lambda _e: self.refresh_stats())
        ttk.Label(self.stats_tab, text="出現率は、そのカードが1枚以上あった対戦の割合だよ。", style="Hint.TLabel").pack(anchor="w", pady=(0, 8))
        cols=("card","initial","final","keep","swap","again")
        self.stats_tree=ttk.Treeview(self.stats_tab,columns=cols,show="headings",height=18)
        labels=("カード名","初手出現率","最終手札出現率","キープ率","交換率","交換後再出現率")
        widths=(240,130,145,120,120,155)
        for c,l,w in zip(cols,labels,widths): self.stats_tree.heading(c,text=l); self.stats_tree.column(c,width=w,anchor="center")
        self.stats_tree.pack(fill="both",expand=True)
        self.stats_tree.tag_configure("odd", background="#f8f5fa")
        self.stats_summary=ttk.Label(self.stats_tab,text="",style="Hint.TLabel"); self.stats_summary.pack(anchor="w",pady=(8,0))

    def build_history(self):
        bar=ttk.Frame(self.history_tab); bar.pack(fill="x",pady=(0,8))
        ttk.Label(bar,text="新しい対戦から表示",style="Hint.TLabel").pack(side="left",padx=(0,16))
        ttk.Button(bar,text="選択した対戦を削除",command=self.delete_match).pack(side="left")
        self.history_tree=ttk.Treeview(self.history_tab,columns=("date","deck","turn","initial","swap","final"),show="headings")
        for c,l,w in [("date","日時",145),("deck","デッキ",130),("turn","手番",65),("initial","初期手札",220),("swap","交換",180),("final","引き直し後",220)]: self.history_tree.heading(c,text=l); self.history_tree.column(c,width=w,anchor="w")
        self.history_tree.tag_configure("odd",background="#f8f5fa")
        self.history_tree.pack(fill="both",expand=True)

    def build_cards(self):
        ttk.Label(self.cards_tab,text="カード名を登録して、画像認識に使う見本を用意するよ。カード一覧はCSVからまとめて追加できる。",style="Hint.TLabel").pack(anchor="w",pady=(0,10))
        row=ttk.Frame(self.cards_tab,style="Card.TFrame",padding=12);row.pack(fill="x",pady=(0,10))
        self.new_card=tk.StringVar()
        ttk.Entry(row,textvariable=self.new_card,width=36).pack(side="left")
        ttk.Button(row,text="カードを追加",command=self.add_card).pack(side="left",padx=8)
        ttk.Button(row,text="CSVを読み込む",command=self.import_csv).pack(side="left")
        ttk.Button(row,text="選択カードの見本画像を登録",command=self.register_template).pack(side="left",padx=8)
        ttk.Button(row,text="選択カードを削除",command=self.remove_card).pack(side="left",padx=8)
        self.cards_list=tk.Listbox(self.cards_tab,height=20,selectmode="extended",font=("Yu Gothic UI",10),background="#ffffff",foreground="#292335",selectbackground="#a33475",selectforeground="#ffffff",borderwidth=0,highlightthickness=1,highlightbackground="#ddd4e2")
        self.cards_list.pack(fill="both",expand=True)
        ttk.Label(self.cards_tab,text="見本はカード全体を選んでね。認識には対象デッキのカード見本が必要だよ。",style="Hint.TLabel").pack(anchor="w",pady=(8,0))

    def card_names(self): return sorted(set(self.data["cards"]),key=str.casefold)

    def refresh_cards(self):
        names=self.card_names()
        if hasattr(self,"initial_boxes"):
            for box in self.initial_boxes: box["values"]=names
            self.update_exchange_ui()
        if hasattr(self,"cards_list"):
            self.cards_list.delete(0,"end")
            self.card_list_names = names
            for name in names:
                mark = "  [見本あり]" if self.data.get("templates", {}).get(name) else "  [見本なし]"
                self.cards_list.insert("end",name+mark)
        if hasattr(self,"stats_filter"):
            current=self.stats_deck.get()
            decks=["すべて"]+sorted({m["deck"] for m in self.data["matches"] if m["deck"]})
            self.stats_filter["values"]=decks
            if current not in decks:self.stats_deck.set("すべて")

    def add_card(self):
        name=self.new_card.get().strip()
        if name and name not in self.data["cards"]:
            self.data["cards"].append(name);self.save();self.refresh_cards()
        self.new_card.set("")

    def import_csv(self):
        path=filedialog.askopenfilename(title="カード一覧CSVを選択",filetypes=[("CSVファイル","*.csv"),("すべてのファイル","*.*")])
        if not path:return
        try:
            with open(path,"r",encoding="utf-8-sig",newline="") as f:
                rows=list(csv.reader(f))
            names=[r[0].strip() for r in rows if r and r[0].strip()]
            if names and names[0].casefold() in {"name","card","card_name","カード名"}:names=names[1:]
            self.data["cards"]=sorted(set(self.data["cards"]+names),key=str.casefold)
            self.save();self.refresh_cards()
            messagebox.showinfo("読み込み完了",f"{len(names)}件のカード名を読み込んだよ。")
        except (OSError,csv.Error) as e:messagebox.showerror("読み込み失敗",str(e))

    def remove_card(self):
        selected=self.cards_list.curselection()
        if not selected:return
        chosen={self.card_list_names[i] for i in selected}
        self.data["cards"]=[c for c in self.data["cards"] if c not in chosen]
        for name in chosen:self.data.get("templates",{}).pop(name,None)
        self.save();self.refresh_cards()

    def register_template(self):
        selected=self.cards_list.curselection()
        if len(selected)!=1:
            messagebox.showinfo("カードを選んでね","見本画像を登録するカードを1枚選択してね。")
            return
        name=self.card_list_names[selected[0]]
        try:
            from screen_reader import capture_card_template
            folder=DATA_DIR/"card_templates"
            folder.mkdir(parents=True,exist_ok=True)
            filename=f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}.png"
            if not capture_card_template(self,folder/filename):return
            self.data.setdefault("templates",{})[name]=filename
            self.save();self.refresh_cards()
            messagebox.showinfo("見本画像を登録したよ",f"「{name}」の画像を保存したよ。")
        except ImportError as e:
            messagebox.showerror("画像認識の準備が必要","画像認識ライブラリが見つからないよ。\n\n"+str(e))
        except Exception as e:
            messagebox.showerror("見本を登録できなかった",str(e))

    def save_match(self):
        initial=[v.get().strip() for v in self.card_vars]
        if any(not x for x in initial):messagebox.showwarning("入力を確認","初期手札4枚をすべて選んでね。");return
        exchanged=[initial[i] for i,v in enumerate(self.exchange_vars) if v.get()]
        redrawn=[v.get().strip() for v in self.redraw_vars]
        if any(not x for x in redrawn):messagebox.showwarning("入力を確認","引き直しで来たカードを選んでね。");return
        m={"id":datetime.now().strftime("%Y%m%d%H%M%S%f"),"date":datetime.now().strftime("%Y-%m-%d %H:%M"),"deck":self.deck_var.get().strip() or "未設定","turn":self.turn_var.get(),"initial":initial,"exchanged":exchanged,"redrawn":redrawn}
        self.data["matches"].append(m)
        for c in initial+redrawn:
            if c not in self.data["cards"]:self.data["cards"].append(c)
        self.save()
        for v in self.card_vars:v.set("")
        for v in self.exchange_vars:v.set(False)
        self.deck_var.set("")
        self.update_exchange_ui();self.refresh_cards();self.refresh_history();self.refresh_stats()
        messagebox.showinfo("保存したよ", "対戦記録を保存したよ♡")

    def recognize_row(self, count):
        try:
            from screen_reader import read_card_row
            templates=self.data.get("templates",{})
            if not templates:
                messagebox.showinfo("見本画像がないよ","先に「カード登録」で対象カードの見本画像を登録してね。")
                return None
            return read_card_row(self,count,templates,DATA_DIR/"card_templates")
        except ImportError as e:
            messagebox.showerror("画像認識の準備が必要", "画面認識ライブラリが見つからないよ。配布版を使うか、開発用の依存関係を入れてね。\n\n" + str(e))
        except Exception as e:
            messagebox.showerror("画面を読み取れなかった", str(e))
        return None

    def capture_initial(self):
        cards = self.recognize_row(4)
        if not cards: return
        for var, card in zip(self.card_vars, cards): var.set(card)
        self.update_exchange_ui()

    def capture_final(self):
        count = sum(v.get() for v in self.exchange_vars)
        if count == 0:
            messagebox.showinfo("交換カードなし", "先に交換する初期手札を選んでね。")
            return
        final = self.recognize_row(4)
        if not final: return
        kept = [self.card_vars[i].get() for i, flag in enumerate(self.exchange_vars) if not flag.get()]
        remaining = list(final)
        for card in kept:
            if card in remaining: remaining.remove(card)
        if len(remaining) != count:
            messagebox.showwarning("確認してね", "読み取った最終手札から交換分を自動で分けきれなかったよ。引き直し欄を確認して直してね。\n\n読み取り結果: " + "、".join(final))
        for var, card in zip(self.redraw_vars, remaining): var.set(card)

    def refresh_history(self):
        if not hasattr(self,"history_tree"):return
        for item in self.history_tree.get_children():self.history_tree.delete(item)
        for index,m in enumerate(reversed(self.data["matches"])):
            self.history_tree.insert("","end",iid=m["id"],values=(m["date"],m["deck"],m["turn"],"、".join(m["initial"]),"、".join(m["exchanged"]) or "なし","、".join(self.final_hand(m))),tags=("odd",) if index % 2 else ())

    @staticmethod
    def final_hand(m):
        result=list(m["initial"])
        for card in m["exchanged"]:
            try: result.remove(card)
            except ValueError: pass
        return result+list(m["redrawn"])

    def delete_match(self):
        sel=self.history_tree.selection()
        if not sel:return
        self.data["matches"]=[m for m in self.data["matches"] if m["id"] not in sel]
        self.save();self.refresh_history();self.refresh_cards();self.refresh_stats()

    def refresh_stats(self):
        if not hasattr(self,"stats_tree"):return
        for item in self.stats_tree.get_children():self.stats_tree.delete(item)
        deck=self.stats_deck.get() if hasattr(self,"stats_deck") else "すべて"
        matches=[m for m in self.data["matches"] if deck=="すべて" or m["deck"]==deck]
        n=len(matches)
        all_cards=set(self.card_names())
        for m in matches:all_cards.update(m["initial"]);all_cards.update(m["redrawn"])
        for card in sorted(all_cards,key=str.casefold):
            initial_games=sum(card in m["initial"] for m in matches)
            final_games=sum(card in self.final_hand(m) for m in matches)
            seen_copies=sum(m["initial"].count(card) for m in matches)
            kept_copies=sum(m["initial"].count(card)-m["exchanged"].count(card) for m in matches)
            exchanged_copies=sum(m["exchanged"].count(card) for m in matches)
            redrawn_copies=sum(m["redrawn"].count(card) for m in matches)
            pct=lambda a,b:f"{(100*a/b):.1f}%" if b else "—"
            self.stats_tree.insert("","end",values=(card,pct(initial_games,n),pct(final_games,n),pct(kept_copies,seen_copies),pct(exchanged_copies,seen_copies),pct(redrawn_copies,exchanged_copies)),tags=("odd",) if len(self.stats_tree.get_children()) % 2 else ())
        self.stats_summary.configure(text=f"対象対戦数: {n}件　|　キープ率・交換率は初手で引いた枚数に対する割合。再出現率は交換した同名カードが引き直しに来た割合。")


if __name__ == "__main__":
    enable_windows_dpi_awareness()
    Tracker().mainloop()
