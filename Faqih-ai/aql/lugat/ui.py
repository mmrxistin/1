# File: Faqih-ai/aql/lugat/ui.py
# Bismillahir Rahmanir Rahim
# El Hamdu Lillah El Hamdulillah
"""aql.lugat.ui — Faqih AI için Tk arayüz.

Ust bolme: AI'a soru yaz (aql.qarar cevaplari).
Alt bolme: Tokenizer/morfoloji detaylari.

Usage:  python3 -m aql.lugat.ui
"""
import tkinter as tk
from tkinter import ttk, scrolledtext

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from aql.lugat.tokenizer import FaqihTokenizer, normalize_text, tokenize
from aql.lugat.morphology import guess_root, morph_analysis
from aql.qarar import answer


class FaqihUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Faqih AI — Sohbet & Tokenizer")
        self.geometry("820x640")
        self.tok = FaqihTokenizer()
        self.tok.train([
            "bismillahirrahmanirrahim",
            "elhamdulillahi rabbil alemin",
            "esselatu ve esselamu alaihi",
            "selamun aleykum merhaba nasilsin",
            "kitap ilim hikmet nur iman salat",
            "merhaba dunya nasilsin bugun hava guzel",
        ], vocab_size=300, iterations=80)

        # ---- ust: sohbet ----
        ttk.Label(self, text="Faqih AI'a soru:").pack(anchor="w", padx=8, pady=(8, 0))
        self.chat = scrolledtext.ScrolledText(self, height=12, state="disabled")
        self.chat.pack(fill="both", expand=True, padx=8, pady=4)

        row = ttk.Frame(self); row.pack(fill="x", padx=8)
        self.entry = ttk.Entry(self)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", lambda e: self.ask())
        ttk.Button(self, text="Gönder", command=self.ask).pack(side="left", padx=4)
        ttk.Button(self, text="Tokenizer detay", command=self.show_tokens).pack(side="left")

        # ---- alt: tokenizer detay ----
        ttk.Label(self, text="Tokenizer / morfoloji detayı:").pack(anchor="w", padx=8, pady=(8, 0))
        self.out = scrolledtext.ScrolledText(self, height=10)
        self.out.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _chat(self, who: str, msg: str) -> None:
        self.chat.configure(state="normal")
        self.chat.insert("end", f"{who}: {msg}\n\n")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def ask(self):
        q = self.entry.get().strip()
        if not q:
            return
        self._chat("Sen", q)
        self.entry.delete(0, "end")
        self._chat("Faqih", answer(q))
        self.detail(q)

    def show_tokens(self):
        q = self.entry.get().strip()
        if q:
            self.detail(q)

    def detail(self, text: str):
        o = self.out
        o.delete("1.0", "end")

        def w(*parts):
            o.insert("end", " ".join(str(p) for p in parts) + "\n")

        w("Normalleştirilmiş:", normalize_text(text, "auto"))
        words = tokenize(text, "auto")
        w("Kelime tokenleri:", words)
        ids = self.tok.encode(text, "auto")
        w("ID dizisi:", ids)
        w("Geri çözüm:", self.tok.decode(ids))
        for word in words[:6]:
            w(f"Kök({word}):", guess_root(word), "| analiz:", morph_analysis(word))


if __name__ == "__main__":
    FaqihUI().mainloop()
