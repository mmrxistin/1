# File: Faqih-ai/aql/qarar/__init__.py
# Bismillahir Rahmanir Rahim
# El Hamdu Lillah El Hamdulillah
"""aql.qarar — Karar/cevap katmanı.

Şimdilik kural tabanlı minik cevap motoru: soruyu tokenizer'dan
geçirir, anahtar kelimeye göre nezaketli bir cevap döndürür.
İleride kelam/mantık katmanları buraya bağlanacak.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from aql.lugat.tokenizer import FaqihTokenizer, normalize_text, tokenize  # noqa: E402

_TOK: FaqihTokenizer | None = None


def _tok() -> FaqihTokenizer:
    global _TOK
    if _TOK is None:
        t = FaqihTokenizer()
        t.train([
            "selamun aleykum merhaba gunaydin iyi aksamlar",
            "bismillahirrahmanirrahim elhamdulillah subhanallah allahu ekber",
            "nasilsin nasiniz ne yapiyorsun bugun hava nasil",
            "kitap ilim hikmet nur iman salat dua sabir sukur",
            "quran ayet sunnet hadis din iman islam",
        ], vocab_size=400, iterations=120)
        _TOK = t
    return _TOK


_RULES: list[tuple[tuple[str, ...], str]] = [
    (("selam", "aleykum", "merhaba", "gunaydin"),
     "Ve aleyküm selam ve rahmetullah. Hoş geldiniz; ne oluruardsa sorabilirisiniz."),
    (("nasilsin", "nasil", "halin"),
     "El Hamdu Lillah, iyi. Siz nasılsınız? Sözünüzü dinlemek üzereyim."),
    (("quran", "ayet"),
     "Kur'ân ayetleri hakkında sorularınızı memnuniyetle alırım; "
     "cevaplarımı mushaf metnine saygı ile, harf harf muhafaza ederek veririm."),
    (("sunnet", "hadis"),
     "Sünnet ve hadis konusundaki sorularınızı alırım; kaynağa sadakat esastır."),
    (("bismillah", "hamd", "subhanallah", "ekber"),
     "Bismillahir Rahmanir Rahim. Sözümüz hayırlı olsun; nasip edersek."),
]


def answer(question: str) -> str:
    """Kural tabanlı minik cevap motoru (yer tutucu; mantiq gelene kadar)."""
    ids = _tok().encode(question)
    words = set(tokenize(question))
    for keys, reply in _RULES:
        if any(k in words for k in keys):
            return reply
    return (f"Sözünüzü aldım ({len(ids)} token). Bu bir yer tutucu cevaptır; "
            "aql.mantiq ve aql.kelam katmanları hazır olduğunda burada "
            "gerçek cevap verilecek.")
