# Bismillahir Rahmanir Rahim
# El Hamdu Lillah El Hamdu Lillah El Hamdulillah
# El Hamdu Lillahi Rabbul Alemin
# Esselatu vesSelamu ala rasulina Muhammedin

"""aql.lugat — Dil katmanı.

Özgün tokenizer (BPE + kelime bazlı melez), Türkçe/Arapça harf
normalizasyonu, kök tahmini (cezd), basit morfoloji.
Sıfırdan yazılmıştır; hazır NLP kütüphanesi kullanılmaz.
"""

from .tokenizer import FaqihTokenizer, normalize_text, tokenize
from .morphology import guess_root, morph_analysis

__all__ = ["FaqihTokenizer", "normalize_text", "tokenize", "guess_root", "morph_analysis"]
