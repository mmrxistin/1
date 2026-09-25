# File: Faqih-ai/aql/lugat/ui.py
# Bismillahir Rahmanir Rahim
# El Hamdu Lillah El Hamdulillah
"""aql.lugat.ui — Tokenizer'i elle denemek icin kucuk Tk arayuz.

Usage:  python3 -m aql.lugat.ui
"""
import tkinter as tk
from tkinter import ttk, scrolledtext

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from aql.lugat.tokenizer import FaqihTokenizer, normalize_text, tokenize
from aql.lugat.morphology import guess_root, morph_analysis


class TokenizerUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Faqih Tokenizer — Elle Deneme")
        self.geometry("780x560")
        self.tok = FaqihTokenizer()
        # Kucuk bir egitim: ornek cumlelerle BPE ogrensin
        self.tok.train([
            "bismillahirrahmanirrahim",
            "elhamdulillahi rabbil alemin",
            "esselatu ve esselamu alaihi",
            "kitap ilim hikmet nur iman salat",
            "merhaba dunya nasilsin bugun hava guzel",
        ], vocab_size=200, iterations=60)

        ttk.Label(self, text="Metin:").pack(anchor="w", padx=8, pady=(8, 0))
        self.input = scrolledtext.ScrolledText(self, height=4)
        self.input.pack(fill="x", padx=8)

        self.lang = tk.StringVar(value="auto")
        row = ttk.Frame(self); row.pack(fill="x", padx=8, pady=4)
        for txt, val in [("Otomatik", "auto"), ("Türkçe", "tr"),
                         ("Arapça", "ar"), ("Ham", "raw")]:
            ttk.Radiobutton(row, text=txt, value=val, variable=self.lang).pack(side="left")

        ttk.Button(self, text="Çalıştır", command=self.run).pack(pady=4)

        self.out = scrolledtext.ScrolledText(self, height=18)
        self.out.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def run(self):
        def w(*parts):
            self.out.insert("end", " ".join(str(p) for p in parts) + "\n")

        text = self.input.get("1.0", "end").strip()
        lang = self.lang.get()
        self.out.delete("1.0", "end")
        if not text:
            return
        w("Normalleştirilmiş:", normalize_text(text, lang))
        w("Kelime tokenleri:", tokenize(text, lang))
        ids = self.tok.encode(text, lang)
        w("FaqihTokenizer ID:", ids)
        w("Geri çözüm:", self.tok.decode(ids))
        for word in tokenize(text, lang):
            root = guess_root(word)
            w(f"Kök({word}):", root, "| analiz:", morph_analysis(word))
        self.out.see("1.0")


if __name__ == "__main__":
    TokenizerUI().mainloop()
