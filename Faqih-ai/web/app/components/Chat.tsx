"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type Msg = { role: "user" | "assistant"; content: string; error?: boolean };
type ChatSes = { id: string; ad: string; mesajlar: Msg[] };

const BOLUMLER = ["kelam", "idrak", "lugat", "tedbir", "iknas"];

const KARSILAMA =
  "Esselamu aleykum. Faqih AI'a hos geldiniz. Sorunuzu yazin veya mikrofona dokunup konusun.";

function yeniSes(no: number): ChatSes {
  return { id: Date.now() + "-" + no, ad: `Yeni Sohbet ${no}`, mesajlar: [] };
}

export default function Chat() {
  const [sohbetler, setSohbetler] = useState<ChatSes[]>([yeniSes(1)]);
  const [aktifId, setAktifId] = useState<string>("");
  const [girdi, setGirdi] = useState("");
  const [bolum, setBolum] = useState("kelam");
  const [yukleniyor, setYukleniyor] = useState(false);
  const [dinliyor, setDinliyor] = useState(false);
  const [konusmaNo, setKonusmaNo] = useState(2);
  const mesajSonu = useRef<HTMLDivElement>(null);
  const tanima = useRef<any>(null);

  useEffect(() => {
    if (!aktifId && sohbetler.length) setAktifId(sohbetler[0].id);
  }, [aktifId, sohbetler]);

  const aktif = sohbetler.find((s) => s.id === aktifId) || sohbetler[0];

  const mesajEkle = useCallback(
    (m: Msg) =>
      setSohbetler((ss) =>
        ss.map((s) =>
          s.id === aktifId
            ? { ...s, mesajlar: [...s.mesajlar, m], ad: s.mesajlar.length === 0 && m.role === "user" ? m.content.slice(0, 30) : s.ad }
            : s
        )
      ),
    [aktifId]
  );

  useEffect(() => {
    mesajSonu.current?.scrollIntoView({ behavior: "smooth" });
  }, [aktif?.mesajlar, yukleniyor]);

  const gonder = useCallback(
    async (metin: string) => {
      const soru = metin.trim();
      if (!soru || yukleniyor || !aktif) return;
      setGirdi("");
      mesajEkle({ role: "user", content: soru });
      setYukleniyor(true);
      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ mesaj: soru, bolum }),
        });
        const data = await res.json();
        mesajEkle(
          res.ok
            ? { role: "assistant", content: data.cevap }
            : { role: "assistant", content: data.error || "Bilinmeyen hata.", error: true }
        );
      } catch {
        mesajEkle({ role: "assistant", content: "Baglanti hatasi.", error: true });
      } finally {
        setYukleniyor(false);
      }
    },
    [aktif, bolum, mesajEkle, yukleniyor]
  );

  // Ses tanima (Web Speech API)
  const dinlemeyiBaslat = useCallback(() => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) {
      alert("Bu tarayici ses tanimayi desteklemiyor. Chrome deneyin.");
      return;
    }
    const tani = new SR();
    tani.lang = "tr-TR";
    tani.continuous = false;
    tani.interimResults = false;
    tani.onresult = (e: any) => {
      const metin = e.results[0][0].transcript;
      setGirdi(metin);
      dinlemeyiDurdur();
      gonder(metin);
    };
    tani.onerror = () => { setDinliyor(false); };
    tani.onend = () => setDinliyor(false);
    tanima.current = tani;
    tani.start();
    setDinliyor(true);
  }, [gonder]);

  const dinlemeyiDurdur = useCallback(() => {
    tanima.current?.stop();
    setDinliyor(false);
  }, []);

  const yeniSohbet = () => {
    const s = yeniSes(konusmaNo);
    setKonusmaNo((n) => n + 1);
    setSohbetler((ss) => [s, ...ss]);
    setAktifId(s.id);
  };

  return (
    <div className="app">
      <aside className="sidebar">
        <h1>Faqih AI</h1>
        <button className="new-chat" onClick={yeniSohbet}>+ Yeni Sohbet</button>
        <div className="chat-list">
          {sohbetler.map((s) => (
            <div key={s.id} className={"chat-item" + (s.id === aktifId ? " active" : "")} onClick={() => setAktifId(s.id)}>
              {s.ad}
            </div>
          ))}
        </div>
      </aside>
      <div className="main">
        <header className="header">
          <label>Bolum:</label>
          <select value={bolum} onChange={(e) => setBolum(e.target.value)} disabled={yukleniyor}>
            {BOLUMLER.map((b) => <option key={b} value={b}>{b}</option>)}
          </select>
        </header>
        <div className="messages">
          {aktif?.mesajlar.length === 0 && (
            <div className="welcome"><h2>{KARSILAMA}</h2></div>
          )}
          {aktif?.mesajlar.map((m, i) => (
            <div key={i} className={"msg " + m.role + (m.error ? " error" : "")}>{m.content}</div>
          ))}
          {yukleniyor && <div className="msg assistant">Dusunuyor...</div>}
          <div ref={mesajSonu} />
        </div>
        <div className="composer">
          <div className="composer-inner">
            <button
              className={"mic-btn" + (dinliyor ? " recording" : "")}
              onClick={dinliyor ? dinlemeyiDurdur : dinlemeyiBaslat}
              disabled={yukleniyor}
              title={dinliyor ? "Dinlemeyi durdur" : "Konustur"}
            >
              {dinliyor ? "●" : "🎤"}
            </button>
            <textarea
              value={girdi}
              onChange={(e) => setGirdi(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); gonder(girdi); }
              }}
              placeholder="Sorunuzu yazin... (Enter: gonder, Shift+Enter: yeni satir)"
              rows={1}
            />
            <button className="send-btn" onClick={() => gonder(girdi)} disabled={yukleniyor || !girdi.trim()}>
              Gonder
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
