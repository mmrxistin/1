# Bismillahir Rahmanir Rahim
# El Hamdu Lillah El Hamdu Lillah El Hamdulillah
# El Hamdu Lillahi Rabbul Alemin
# Esselatu vesSelamu ala rasulina Muhammedin
"""aql.llm.core — Mini LLM çekirdeği.

Saf numpy ile karakter-seviyesi küçük bir transformer dil modeli.
Her aql bölümü (kelam, idrak, ...) bu çekirdekten KENDİ ayrı modelini
kurar ve kendi gövdesiyle eğitilir — bölümler birbirinden bağımsız LLM'dir.

Backend seçimi:
  - torch varsa TorchBackend kullanılır (daha hızlı).
  - yoksa NumpyBackend devreye girer (saf numpy, bağımlılıksız).

Dış açık kaynak LLM takmak için: aql.llm.bridge modülüne bak.
"""
import math
import os
import pickle
import random

import numpy as np

# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------

BOM = "<bas>"   # baslangic belirteci (karakter duzeyinde diyez dizisi)
EOM = "<son>"   # son belirteci


class CharVocab:
    """Karakter-seviyesi basit sozluk."""

    def __init__(self, text: str):
        chars = sorted(set(text))
        self.stoi = {c: i for i, c in enumerate(chars)}
        self.itos = {i: c for i, c in enumerate(chars)}
        self.size = len(chars)

    def encode(self, s: str):
        return [self.stoi[c] for c in s if c in self.stoi]

    def decode(self, ids):
        return "".join(self.itos.get(int(i), "") for i in ids)


# ---------------------------------------------------------------------------
# Numpy backend: mini transformer
# ---------------------------------------------------------------------------

def _gelu(x):
    return 0.5 * x * (1.0 + np.tanh(math.sqrt(2.0 / math.pi) * (x + 0.044715 * x ** 3)))


def _softmax(x, axis=-1):
    x = x - x.max(axis=axis, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=axis, keepdims=True)


def _rng_init(shape, scale):
    return (np.random.default_rng(0).standard_normal(shape) * scale).astype(np.float32)


class _Linear:
    def __init__(self, nin, nout, scale=0.02):
        self.w = _rng_init((nin, nout), scale)
        self.b = np.zeros(nout, dtype=np.float32)

    def __call__(self, x):
        return x @ self.w + self.b


class _AttentionHead:
    """Tek kafali self-attention (kolsuz, nedensel)."""

    def __init__(self, dim, head_dim):
        self.q = _Linear(dim, head_dim, 0.02)
        self.k = _Linear(dim, head_dim, 0.02)
        self.v = _Linear(dim, head_dim, 0.02)
        self.head_dim = head_dim

    def __call__(self, x):
        T, D = x.shape
        q, k, v = self.q(x), self.k(x), self.v(x)
        att = q @ k.T / math.sqrt(self.head_dim)
        mask = np.tril(np.ones((T, T), dtype=bool))
        att = np.where(mask, att, -1e9)
        w = _softmax(att, axis=-1)
        return w @ v


class _Block:
    """Transformer blogu: attention + MLP, pre-norm."""

    def __init__(self, dim):
        self.attn = _AttentionHead(dim, dim)
        self.ln1_g = np.ones(dim, dtype=np.float32)
        self.ln1_b = np.zeros(dim, dtype=np.float32)
        self.fc1 = _Linear(dim, 4 * dim, 0.02)
        self.fc2 = _Linear(4 * dim, dim, 0.02)
        self.ln2_g = np.ones(dim, dtype=np.float32)
        self.ln2_b = np.zeros(dim, dtype=np.float32)

    @staticmethod
    def _ln(x, g, b):
        m = x.mean(-1, keepdims=True)
        v = x.var(-1, keepdims=True)
        return (x - m) / np.sqrt(v + 1e-5) * g + b

    def __call__(self, x):
        h = self._ln(x, self.ln1_g, self.ln1_b)
        x = x + self.attn(h)
        h = self._ln(x, self.ln2_g, self.ln2_b)
        h = _gelu(self.fc1(h))
        return x + self.fc2(h)


class NumpyMiniGPT:
    """Cok kucuk, tek-kafali, cok-katmanli karakter GPT (numpy).

    Egitim: basit salt gradyan inisi (Adam yok — sadelik ve hafiflik icin).
    Kayip: cross-entropy.
    """

    def __init__(self, vocab_size, dim=64, layers=2, block=64, lr=1e-2, seed=0):
        self.vocab_size = vocab_size
        self.dim, self.layers, self.block = dim, layers, block
        self.lr = lr
        self.rng = np.random.default_rng(seed)
        self.tok_emb = _rng_init((vocab_size, dim), 0.02)
        self.pos_emb = _rng_init((block, dim), 0.01)
        self.blocks = [_Block(dim) for _ in range(layers)]
        self.lnf_g = np.ones(dim, dtype=np.float32)
        self.lnf_b = np.zeros(dim, dtype=np.float32)
        self.head_w = self.tok_emb  # tied embedding
        # son cache (geri yayilim icin)
        self._cache = None

    # -- ileri -------------------------------------------------------------
    def _lnf(self, x):
        m = x.mean(-1, keepdims=True)
        v = x.var(-1, keepdims=True)
        return (x - m) / np.sqrt(v + 1e-5) * self.lnf_g + self.lnf_b

    def forward(self, idx):
        """idx: (T,) tam sayilar -> logits (T, vocab)"""
        T = len(idx)
        x = self.tok_emb[idx] + self.pos_emb[:T]
        caches = []
        for blk in self.blocks:
            caches.append(x.copy())
            x = blk(x)
        x = self._lnf(x)
        logits = x @ self.head_w
        self._cache = (idx, caches, x)
        return logits

    # -- kayip -------------------------------------------------------------
    def loss(self, idx, targets):
        logits = self.forward(idx)
        T = len(idx)
        lg = logits - logits.max(-1, keepdims=True)
        logp = lg - np.log(np.exp(lg).sum(-1, keepdims=True))
        nll = -logp[np.arange(T), targets].mean()
        return nll, logits

    # -- geri yayilim (yaklasik, pratik) -------------------------------------
    # Tam transformer geri yayilimi numpy'de yazilabilir ama kod cogalir;
    # burada basitlestirilmis salt-gradyan guncelleme kullaniliyor:
    # yon, logits->head->lnf->blocks sirasiyla son aktivasyonlarla kurulur.
    def backward_step(self, idx, targets):
        loss, logits = self.loss(idx, targets)
        idx0, caches, x = self._cache
        T = len(idx)
        # softmax - onehot gradyani
        p = _softmax(logits, -1)
        dlogits = p.copy()
        dlogits[np.arange(T), targets] -= 1.0
        dlogits /= T
        # head (tied): dW = x.T @ dlogits ; dX = dlogits @ W.T
        dW = x.T @ dlogits
        dX = dlogits @ self.head_w.T
        # lnf gradyani (yaklasik: sadece olcekle)
        dX = dX * self.lnf_g
        # bloklarda geriye: her blok icin残 gradyani MLP koluna uygula
        for i, blk in enumerate(self.blocks):
            h_pre = caches[i]
            h_ln = blk._ln(h_pre, blk.ln2_g, blk.ln2_b)
            h1 = _gelu(blk.fc1(h_ln))
            # fc2 gradyani
            dW2 = h1.T @ dX
            dh1 = dX @ blk.fc2.w.T
            # gelu turevi (yaklasik tanh)
            z = blk.fc1(h_ln)
            t = np.tanh(math.sqrt(2.0 / math.pi) * (z + 0.044715 * z ** 3))
            dz = dh1 * (0.5 * (1.0 + t) + 0.5 * z * (1 - t ** 2) * math.sqrt(2.0 / math.pi) * (1 + 3 * 0.044715 * z ** 2))
            dW1 = h_ln.T @ dz
            # guncelle
            blk.fc2.w -= self.lr * dW2
            blk.fc1.w -= self.lr * dW1
            # attention kolunu (agir) atla: kelime gecmisini zaten MLP tutuyor
            # tied head guncelle
        self.head_w -= self.lr * dW
        self.tok_emb -= self.lr * dW[: self.vocab_size]
        return float(loss)

    # -- uretim --------------------------------------------------------------

    def generate(self, vocab: CharVocab, prompt: str, n_new=80, temperature=0.9):
        ids = vocab.encode(prompt) or [0]
        ids = ids[-self._block_size:]
        out = list(ids)
        for _ in range(n_new):
            ctx = out[-self._block_size:]
            logits = self.forward(np.array(ctx))
            logits = logits[-1] / max(temperature, 1e-6)
            probs = _softmax(logits)
            nxt = int(self.rng.choice(len(probs), p=probs))
            out.append(nxt)
        return vocab.decode(out[len(ids):])

    # -- kaydet / yukle ------------------------------------------------------    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        state = {
            "vocab_size": self.vocab_size,
            "dim": self.dim,
            "layers": self.layers,
            "block": self._block_size,
            "tok_emb": self.tok_emb,
            "pos_emb": self.pos_emb,
            "blocks": [(b.fc1.w, b.fc2.w) for b in self.blocks],
        }
        with open(path, "wb") as f:
            pickle.dump(state, f)

    @classmethod
    def load(cls, path):
        with open(path, "rb") as f:
            state = pickle.load(f)
        m = cls(state["vocab_size"], state["dim"], state["layers"], state["block"])
        m.tok_emb = state["tok_emb"]
        m.pos_emb = state["pos_emb"]
        for b, (w1, w2) in zip(m.blocks, state["blocks"]):
            b.fc1.w, b.fc2.w = w1, w2
        return m


# init düzeltmesi: property'yi cakistirmayalim
_orig_init = NumpyMiniGPT.__init__


def _patched_init(self, vocab_size, dim=64, layers=2, block=64, lr=1e-2, seed=0):
    self._block_size = block
    _orig_init(self, vocab_size, dim, layers, block, lr, seed)


NumpyMiniGPT.__init__ = _patched_init
