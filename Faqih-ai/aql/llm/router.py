# Bismillahir Rahmanir Rahim
# El Hamdu Lillah El Hamdu Lillah El Hamdulillah
# El Hamdu Lillahi Rabbul Alemin
# Esselatu vesSelamu ala rasulina Muhammedin
"""aql.llm.router — Soruyu doğru bölüm LLM'ine yönlendirir.

Anahtar kelime skoru ile en uygun bölümü seçer; cem bölümü
diğerlerinin cevaplarını birleştirip topluca cevap kurar.
"""
import re
from .sections import hepsini_olustur

# bölüm -> anahtar kelimeler
ANAHTARLAR = {
    "kelam": ("selam", "sohbet", "konus", "söyle", "soyle", "merhaba", "soz", "söz"),
    "idrak": ("mana", "anlam", "kavra", "idrak", "anla", "oz", "derin", "tevkill"),
    "lugat": ("kok", "kök", "kelime", "lugat", "sozluk", "ek", "kalip", "mecaz"),
    "mantiq": ("neden", "nicin", "mantiq", "akil", "akıl", "kiyas", "onerme", "sonuc", "if"),
    "qarar": ("karar", "qarar", "hukum", "hüküm", "ver", "gerekli", "olmali", "onay"),
    "cer": ("elestir", "itiraz", "tez", "antitez", "aksini", "cer", "neden olmaz"),
}

_YUK = None


def _yukle():
    """Tüm bölüm LLM'lerini yükle; kayıtlı model varsa diskten, yoksa eğit."""
    global _YUK
    if _YUK is None:
        _YUK = {}
        for b in hepsini_olustur():
            if not b.yukle():
                b.egit()
                b.kaydet()
            _YUK[b.ad] = b
    return _YUK


def sec(metin: str) -> str:
    """Metne en uygun bölüm adını döndürür."""
    m = metin.lower()
    skor = {ad: sum(1 for k in keys if k in m) for ad, keys in ANAHTARLAR.items()}
    en_iyi = max(skor, key=skor.get)
    return en_iyi if skor[en_iyi] > 0 else "kelam"  # varsayilan: kelam


def sor(metin: str, tek_bolum=True) -> dict:
    """Metni iletir; {bolum: cevap} dondurur.

    tek_bolum=True ise sadece secilen bölüm cevap verir.
    tek_bolum=False ise tüm bölümler cevaplar + cem birleştirir.
    """
    modeller = _yukle()
    if tek_bolum:
        ad = sec(metin)
        cevaplar = {ad: modeller[ad].sor(metin)}
    else:
        cevaplar = {ad: b.sor(metin) for ad, b in modeller.items() if ad != "cem"}
        cevaplar["cem"] = modeller["cem"].sor(" ".join(cevaplar.values()))
    return cevaplar
