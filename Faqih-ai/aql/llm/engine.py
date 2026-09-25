# Bismillahir Rahmanir Rahim
# El Hamdu Lillah El Hamdu Lillah El Hamdulillah
# El Hamdu Lillahi Rabbul Alemin
# Esselatu vesSelamu ala rasulina Muhammedin
"""aql.llm.engine — Bölüm LLM'i sarmalayıcı ve eğitici.

Her bölüm (kelam, idrak, ...) için AYRI bir mini GPT örneği kurar,
kendi gövdesiyle (persona + ders metinleri) eğitir, diske kaydeder.
"""
import os
import random

from .core import CharVocab, NumpyMiniGPT

MODELLER_DIR = os.path.join(os.path.dirname(__file__), "modeller")


def egit(metin: str, adim: int = 150, dim: int = 48, layers: int = 2,
         block: int = 48, lr: float = 5e-2, seed: int = 0, log: bool = False):
    """Verilen metin uzerine mini LLM egitir; (model, vocab) dondurur."""
    vocab = CharVocab(metin)
    if vocab.size < 4:
        raise ValueError("Metin cok kisa/cesitsiz; egitim icin daha genis metin gerekli.")
    model = NumpyMiniGPT(vocab.size, dim=dim, layers=layers, block=block, lr=lr, seed=seed)
    data = vocab.encode(metin)
    rng = random.Random(seed)
    for adim_no in range(adim):
        i = rng.randint(0, max(0, len(data) - block - 1))
        ctx = data[i:i + block]
        tgt = data[i + 1:i + block + 1]
        if len(tgt) < len(ctx):
            continue
        kayip = model.backward_step(ctx, tgt)
        if log and adim_no % 25 == 0:
            print(f"  adim {adim_no:4d}  kayip {kayip:.3f}")
    return model, vocab


class BolumLLM:
    """Tek bir bölümün kendi LLM'i (kelam, idrak, ...)."""

    def __init__(self, ad: str, persona: str, egitim_metni: str,
                 dim=48, layers=2, block=48, adim=150):
        self.ad = ad
        self.persona = persona
        self.egitim_metni = persona + "\n" + egitim_metni
        self.dim, self.layers, self.block, self.adim = dim, layers, block, adim
        self.model = None
        self.vocab = None

    def egit(self, log=False):
        self.model, self.vocab = egit(
            self.egitim_metni, adim=self.adim, dim=self.dim,
            layers=self.layers, block=self.block, seed=hash(self.ad) % 2**31)
        if log:
            print(f"[{self.ad}] egitildi.")
        return self

    def kaydet(self):
        os.makedirs(MODELLER_DIR, exist_ok=True)
        self.model.save(os.path.join(MODELLER_DIR, f"{self.ad}.pkl"))

    def yukle(self) -> bool:
        yol = os.path.join(MODELLER_DIR, f"{self.ad}.pkl")
        if os.path.exists(yol):
            self.model = NumpyMiniGPT.load(yol)
            self.vocab = CharVocab(self.egitim_metni)
            return True
        return False

    def hazir_mi(self) -> bool:
        return self.model is not None

    def sor(self, metin: str, n_new=100, temperature=0.9) -> str:
        """Bu bölümün kendi LLM'i ile uretir."""
        if not self.hazir_mi():
            raise RuntimeError(f"[{self.ad}] modeli henuz egitilmemis.")
        return self.model.generate(self.vocab, metin, n_new=n_new, temperature=temperature)

    def __repr__(self):
        durum = "hazir" if self.hazir_mi() else "egitimsiz"
        return f"<BolumLLM {self.ad} ({durum})>"
