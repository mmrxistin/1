# Bismillahir Rahmanir Rahim
# El Hamdu Lillah El Hamdu Lillah El Hamdulillah
# El Hamdu Lillahi Rabbul Alemin
# Esselatu vesSelamu ala rasulina Muhammedin

"""aql.lugat.morphology — Basit kök tahmini (cezd) ve morfoloji.

Kural tabanlı, Türkçe ve Arapça için. Sözlük yoksa (OOP) sezgisel
(heuristic) kurallarla kök tahmini yapılır — hakiki lugat için
sonradan sözlük verisi eklenebilir.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

# Türkçe ekler — uzundan kısaya siralanmis
_TR_SUFFIXES = [
    "larımızdan", "lerimizden", "larımızda", "larımızın", "lerimizden",
    "larının", "larında", "larından", "larımız", "lerimiz",
    "larda", "lerden", "ların", "ların", "ları", "leri",
    "nın", "nin", "nun", "nün", "nda", "nde", "ndan", "nden",
    "da", "de", "dan", "den", "ta", "te", "tan", "ten",
    "ın", "in", "un", "ün", "ım", "im", "um", "üm",
    "sı", "si", "su", "sü", "ları", "ı", "i", "u", "ü",
    "a", "e", "ya", "ye",
]

_AR_SUFFIXES = [
    "والون", "والون", "ون", "ات", "ان", "ين", "هم", "كم", "نا", "ها", "هن",
    "ي", "ك", "ه",
]

_AR_PREFIXES = ["ال", "و", "ف", "ب", "ل", "لل", "وب", "فال", "بال", "وال"]


def _strip_suffixes(word: str, suffixes: List[str], min_len: int = 3) -> str:
    changed = True
    while changed and len(word) > min_len:
        changed = False
        for suf in sorted(suffixes, key=len, reverse=True):
            if word.endswith(suf) and len(word) - len(suf) >= min_len:
                word = word[: -len(suf)]
                changed = True
                break
    return word


def _strip_prefixes(word: str, prefixes: List[str]) -> str:
    for pre in sorted(prefixes, key=len, reverse=True):
        if word.startswith(pre) and len(word) - len(pre) >= 3:
            return word[len(pre):]
    return word


def guess_root(word: str, lang: str = "auto") -> Dict:
    """Kök (cezd) tahmini. Döner: {word, root, lang, confidence}."""
    if lang == "auto":
        has_arabic = any("\u0600" <= c <= "\u06FF" for c in word)
        lang = "ar" if has_arabic else "tr"
    original = word
    if lang == "tr":
        root = _strip_suffixes(word, _TR_SUFFIXES)
        root = _strip_prefixes(root, ["ki", "mi", "da", "de"])
        # vokal duseyirmi? Hayir — koku koruyoruz (yapisal kok = sadelestirilmis)
        confidence = 0.55 if root != original else 0.75
    else:  # ar
        root = _strip_prefixes(word, _AR_PREFIXES)
        root = _strip_suffixes(root, _AR_SUFFIXES)
        # Arapça: üc harfli kok icin orta harflerindeki kuvvet harfleri
        confidence = 0.5 if root != original else 0.7
    return {"word": original, "root": root, "lang": lang, "confidence": confidence}


def morph_analysis(text: str, lang: str = "auto") -> List[Dict]:
    """Tüm kelimeler için basit morfolojik analiz."""
    from .tokenizer import tokenize
    out: List[Dict] = []
    for w in tokenize(text, lang):
        r = guess_root(w, lang)
        # biraz da tur bilgisini yazalim
        kind = "isim"
        if lang == "tr" and re.search(r"(mek|mak|yor|dı|di|du|dü|mış|miş|muş|müş)$", r["root"]):
            kind = "fiil"
        out.append({
            "word": r["word"],
            "root": r["root"],
            "kind": kind,
            "confidence": r["confidence"],
        })
    return out
