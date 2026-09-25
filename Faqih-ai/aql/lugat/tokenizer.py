# Bismillahir Rahmanir Rahim
# El Hamdu Lillah El Hamdu Lillah El Hamdulillah
# El Hamdu Lillahi Rabbul Alemin
# Esselatu vesSelamu ala rasulina Muhammedin

# File: Faqih-ai/aql/lugat/tokenizer.py
"""aql.lugat.tokenizer — Özgün melez tokenizer.

Kelime bazlı hazine + karakter bazlı BPE melezi. Türkçe ve Arapça
destekler. Sıfırdan yazılmıştır (hazır tokenizer yok).
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Tuple

# ------------------------------------------------------------------
# Harf normalizasyonu — Türkçe ve Arapça
# ------------------------------------------------------------------

_TURKISH_MAP = str.maketrans({
    "ı": "i", "İ": "I", "ş": "s", "Ş": "S", "ğ": "g", "Ğ": "G",
    "ü": "u", "Ü": "U", "ö": "o", "Ö": "O", "ç": "c", "Ç": "C",
})

_ARABIC_MAP = str.maketrans({
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",   # elif varyantlari
    "ة": "ه",                                  # te marbuta -> ha
    "ى": "ي",                                  # elif maksura -> ya
    "ئ": "ي", "ؤ": "و",                        # elif-vav birlesikleri
})

# Tehlike: teshil isaretleri (harakat) U+064B..U+065F, tenvin, shadda
_HARAKAT_RE = re.compile(r"[\u064B-\u065F\u0670\u06D6-\u06ED]")


def normalize_text(text: str, lang: str = "auto") -> str:
    """Metni normalleştirir: harakat düşürür, elif/elif-vav birleştirir,
    Türkçe harfleri Latin temeline indirir. `lang`: auto|tr|ar|raw."""
    if lang == "raw":
        return text
    if lang == "auto":
        has_arabic = any("\u0600" <= c <= "\u06FF" for c in text)
        lang = "ar" if has_arabic else "tr"
    if lang == "ar":
        text = _HARAKAT_RE.sub("", text)
        text = text.translate(_ARABIC_MAP)
    elif lang == "tr":
        text = text.translate(_TURKISH_MAP)
    text = unicodedata.normalize("NFC", text)
    return text.strip()


_TOKEN_RE = re.compile(r"[\w\u0600-\u06FF]+", re.UNICODE)


def tokenize(text: str, lang: str = "auto") -> List[str]:
    """Basit kelime tokenize: harfler/rakamlar + Arapça aralığı."""
    norm = normalize_text(text, lang)
    return _TOKEN_RE.findall(norm)


# ------------------------------------------------------------------
# BPE — karakter bazlı, özgün uygulama
# ------------------------------------------------------------------

_WORD_END = "</w>"


@dataclass
class FaqihTokenizer:
    """Melez tokenizer: önce kelime hazinesi (vocab), olmayanlar için BPE.

    Usage:
        tok = FaqihTokenizer()
        tok.train(corpus, vocab_size=2000, iterations=200)
        ids = tok.encode("bismillah")
        text = tok.decode(ids)
    """

    vocab: Dict[str, int] = field(default_factory=dict)
    merges: List[Tuple[str, str]] = field(default_factory=list)
    special_tokens: Dict[str, int] = field(default_factory=dict)

    # --- özel tokenler ---
    def _ensure_specials(self) -> None:
        if self.special_tokens:
            return
        specials = ["<pad>", "<unk>", "<bos>", "<eos>", "<sep>",
                    "<quran>", "<sunnet>", "<soru>", "<cevap>"]
        for s in specials:
            self.special_tokens[s] = len(self.vocab)
            self.vocab[s] = len(self.vocab)

    # --- eğitim ---
    def train(self, corpus: Iterable[str], vocab_size: int = 1000,
              iterations: int = 100, lang: str = "auto") -> None:
        self._ensure_specials()
        words = Counter()
        for line in corpus:
            for w in tokenize(line, lang):
                words[w] += 1
        # BPE sembollerini kelime sonu isaretiyle kur
        symbol_seqs = {w: list(w) + [_WORD_END] for w in words}
        # Temel alfabe: tum tek karakterler vocab'e girsin ki
        # decode '<unk>' ile dolmasin (BPE tabani).
        for seq in symbol_seqs.values():
            for ch in seq:
                if ch not in self.vocab:
                    self.vocab[ch] = len(self.vocab)
        for _ in range(iterations):
            if len(self.vocab) >= vocab_size:
                break
            pair_freq: Counter = Counter()
            for w, freq in words.items():
                seq = symbol_seqs[w]
                for a, b in zip(seq, seq[1:]):
                    pair_freq[(a, b)] += freq
            if not pair_freq:
                break
            (a, b), _ = pair_freq.most_common(1)[0]
            self.merges.append((a, b))
            self.vocab[a + b] = len(self.vocab)
            for w in words:
                seq = symbol_seqs[w]
                i = 0
                new_seq: List[str] = []
                while i < len(seq):
                    if i < len(seq) - 1 and seq[i] == a and seq[i + 1] == b:
                        new_seq.append(a + b)
                        i += 2
                    else:
                        new_seq.append(seq[i])
                        i += 1
                symbol_seqs[w] = new_seq

    # --- kodlama ---
    def _bpe_word(self, word: str) -> List[str]:
        seq = list(word) + [_WORD_END]
        for a, b in self.merges:
            i = 0
            new_seq: List[str] = []
            while i < len(seq):
                if i < len(seq) - 1 and seq[i] == a and seq[i + 1] == b:
                    new_seq.append(a + b)
                    i += 2
                else:
                    new_seq.append(seq[i])
                    i += 1
            seq = new_seq
        return seq

    def encode(self, text: str, lang: str = "auto",
               add_specials: Tuple[str, ...] = ()) -> List[int]:
        ids: List[int] = []
        for s in add_specials:
            ids.append(self.special_tokens[s])
        for w in tokenize(text, lang):
            if w in self.vocab:
                ids.append(self.vocab[w])
            else:
                for piece in self._bpe_word(w):
                    pid = self.vocab.get(piece)
                    if pid is None:
                        # Buyuk/kucuk harf yedegi: alfabede olmayan buyuk
                        # harfler <unk>'a dusmesin.
                        pid = self.vocab.get(piece.lower())
                    if pid is None:
                        for ch in piece:
                            pid = self.vocab.get(ch)
                            if pid is None:
                                pid = self.vocab.get(ch.lower())
                            if pid is None:
                                pid = self.special_tokens["<unk>"]
                            ids.append(pid)
                        continue
                    ids.append(pid)
        return ids

    def decode(self, ids: Iterable[int]) -> str:
        inv = {v: k for k, v in self.vocab.items()}
        pieces = [inv.get(i, "") for i in ids]
        text = "".join(pieces)
        return text.replace(_WORD_END, " ").strip()

    def save(self, path: str) -> None:
        import json
        data = {"vocab": self.vocab, "merges": [list(m) for m in self.merges]}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)

    @classmethod
    def load(cls, path: str) -> "FaqihTokenizer":
        import json
        tok = cls()
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        tok.vocab = {k: int(v) for k, v in data["vocab"].items()}
        tok.merges = [(a, b) for a, b in data["merges"]]
        return tok
