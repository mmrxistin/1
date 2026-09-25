# Bismillahir Rahmanir Rahim
# El Hamdu Lillah El Hamdu Lillah El Hamdulillah
# El Hamdu Lillahi Rabbul Alemin
# Esselatu vesSelamu ala rasulina Muhammedin
"""aql.llm — Bölümlere ayrılmış mini LLM paketi.

  core     : saf numpy mini transformer (torch yoksa bile çalışır)
  engine   : BolumLLM sarmalayıcı ve eğitici
  sections : her bölümün kişilik gövdesi + tohum corpus
  router   : soruyu doğru bölüm LLM'ine yönlendirme
  bridge   : llama.cpp / Ollama gibi açık kaynak LLM takma köprüsü

Kullanım:
    from aql.llm import router
    cevaplar = router.sor("selamun aleykum")
    cevaplar = router.sor("kok nedir", tek_bolum=False)  # tüm bölümler
"""
from .core import CharVocab, NumpyMiniGPT
from .engine import BolumLLM, egit
from .sections import hepsini_olustur
from . import router

__all__ = ["CharVocab", "NumpyMiniGPT", "BolumLLM", "egit",
           "hepsini_olustur", "router"]
