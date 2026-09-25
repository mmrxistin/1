# Bismillahir Rahmanir Rahim
# El Hamdu Lillah El Hamdu Lillah El Hamdulillah
# El Hamdu Lillahi Rabbul Alemin
# Esselatu vesSelamu ala rasulina Muhammedin
"""aql.qarar — Karar/cevap katmanı.
Kural tabanlı minik cevap motoru + SON CEVAP DENETİMİ (revizyon).
Kural: Verilecek son cevap, Allah'a ve O'nun ayetlerine saygısızlık
manasına gelebilecek her türlü ifade bakımından denetlenir; şüpheli
tek kelime varsa cevap yeniden düzenlenir, ondan sonra verilir.
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


# ------------------------------------------------------------------
# SON CEVAP DENETİMİ — yüzde yüz hassasiyet hedefi
# ------------------------------------------------------------------

# Not: Liste yalnız gerçekten saygısızlık/hakaret manası taşıyan
# kelimeleri içerir. Masum ve hayırlı kelimeler (selam, hamd, sevgi,
# tövbe, yardım, kardeş, "ne/nasıl" gibi soru kelimeleri) asla yasak
# değildir; onları yasaklamak cevap kalitesini bozar.
_YASAK_KELİME = {
    # hakaret/küfür
    "aptal", "ahmak", "salak", "gerizekalı", "eşek", "domuz", "hain",
    "yalancı", "nankör", "yobaz", "şerefsiz", "kahpe",
    # Allah'a/ayetlere yönelik saygısızlık manası
    "sahte", "uydurma", "uyduruk", "hurafe", "hurafeli", "batıl",
    "abes", "saçmalık", "lüzumsuz", "kerahet", "kerahetle",
    "küfür", "küfr", "lanet", "lanetledi",
}

# Bölünmüş kesin yasak: ardışık iki kelime olarak aranır.
_YASAK_İKİLİ = {
    ("allah", "yok"), ("allah", "yalan"), ("allah", "gül"), ("allah", "şaş"),
    ("ayet", "yalan"), ("ayet", "şaka"), ("ayet", "gül"), ("ayet", "doldur"),
    ("quran", "yalan"), ("quran", "şaka"), ("quran", "gül"), ("quran", "doldur"),
    ("kafir", "sen"), ("müşrik", "sen"), ("hain", "sen"), ("yalancı", "sen"),
    ("aptal", "sen"), ("ahmak", "sen"), ("salak", "sen"), ("cahil", "sen"),
    ("koyun", "sen"), ("eşek", "sen"), ("domuz", "sen"), ("gerizekalı", "sen"),
    ("inanmayan", "sen"), ("nankör", "sen"), ("zalim", "sen"),
}




def _cevap_denetle(metin: str) -> bool:
    """Verilecek son cevabı denetler: Allah'a ve O'nun ayetlerine
    saygısızlık manasına gelebilecek en ufak ibare varsa False döner.
    Yüzde yüz hassasiyet hedefi: kural tabanlı + ikili eşleşme + sabit
    yazım denetimi; şüpheli her durumda cevap yeniden düzenlenir."""
    if not metin or not metin.strip():
        return False
    kelimeler = tokenize(metin, lang="raw")
    norm = normalize_text(metin, lang="raw").lower()
    # 1) kesin yasak çıplak kelime
    for k in kelimeler:
        if k in _YASAK_KELİME:
            return False
    # 2) ikili (ardışık kelime) saygısızlık kalıbı
    for a, b in zip(kelimeler, kelimeler[1:]):
        if (a, b) in _YASAK_İKİLİ:
            return False

    # 3) Hz. Muhammed (s.a.v.) için eksik/bağlantısız yazım engellenir.
    if "aleyhi" in norm and "aleyhisselam" not in norm \
            and "aleyhi selam" not in norm \
            and "aleyhi ve sellem" not in norm:
        return False
    # 4) tekrar normalizasyon gereksizdi; tek sefer yapılır (satır 75).
    return True


# ------------------------------------------------------------------
# KURAL TABANLI CEVAP MOTORU
# ------------------------------------------------------------------

_RULES: list[tuple[tuple[str, ...], str]] = [
    (("selam", "aleykum", "merhaba", "gunaydin"),
     "Ve aleyküm selam ve rahmetullah. Hoş geldiniz; ne sorarsanız sorabilirsiniz."),
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

# Kural bulamazsak verilecek yer tutucu — denetimi geçecek şekilde yazıldı.
_YEDEK_CEVAP = ("El Hamdu Lillah. Sorunuzu aldım; kaynağa sadakat ile, "
                 "harf harf muhafaza ederek cevap vereceğim.")


def _cevap(question: str) -> str:
    """Kural tabanlı minik cevap motoru; son cevap daima denetlenir."""
    words = set(tokenize(question))
    cevap: str | None = None
    for keys, reply in _RULES:
        if any(k in words for k in keys):
            cevap = reply
            break
    if cevap is None:
        cevap = _YEDEK_CEVAP
    # --- SON CEVAP DENETİMİ ---
    # Yüzde yüz hassasiyet: cevapta Allah-u Teâlâ'ya ve ayetlerine
    # saygısızlık manasına gelebilecek hiçbir yanlışlık kalmamalı.
    if not _cevap_denetle(cevap):
        cevap = _YEDEK_CEVAP
        if not _cevap_denetle(cevap):  # yedek bile hatalıysa:
            cevap = "El Hamdu Lillah. Cevabımı kaynağa sadakat ile vereceğim."
    return cevap
