# Bismillahir Rahmanir Rahim
# El Hamdu Lillah El Hamdu Lillah El Hamdulillah
# El Hamdu Lillahi Rabbul Alemin
# Esselatu vesSelamu ala rasulina Muhammedin
"""aql.llm.bridge — Açık kaynak LLM takma köprüsü.

Mini LLM yerine (veya yanına) açık kaynak modeller bağlanabilir:
  - llama.cpp (gguf)     -> LlamaCppBridge
  - Ollama               -> OllamaBridge
  - HuggingFace/transformers -> HFBridge

Her köprü, BolumLLM ile aynı arayüze uyar (sor() metodu), böylece
router fark etmeden büyük model kullanabilir.
"""
import json
import urllib.request


class LlamaCppBridge:
    """llama.cpp sunucusuna (llama-server, default 8080) baglanir."""

    def __init__(self, ad, host="http://127.0.0.1:8080", persona=""):
        self.ad = ad
        self.host = host.rstrip("/")
        self.persona = persona

    def hazir_mi(self):
        return True

    def sor(self, metin, n_new=200, temperature=0.8):
        payload = {
            "prompt": f"{self.persona}\nSoru: {metin}\nCevap:",
            "n_predict": n_new,
            "temperature": temperature,
            "stop": ["\nS:"],
        }
        req = urllib.request.Request(
            self.host + "/completion",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())["content"]


class OllamaBridge:
    """Ollama (default 11434) uzerinden model sorar."""

    def __init__(self, ad, model="llama3.2", host="http://127.0.0.1:11434", persona=""):
        self.ad = ad
        self.model = model
        self.host = host.rstrip("/")
        self.persona = persona

    def hazir_mi(self):
        return True

    def sor(self, metin, n_new=200, temperature=0.8):
        payload = {
            "model": self.model,
            "prompt": f"{self.persona}\nSoru: {metin}\nCevap:",
            "stream": False,
            "options": {"temperature": temperature, "num_predict": n_new},
        }
        req = urllib.request.Request(
            self.host + "/api/generate",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read())["response"]


def dis_bolum_adlari():
    return ["llamacpp", "ollama"]
