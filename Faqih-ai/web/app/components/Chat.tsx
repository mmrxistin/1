"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type Msg = { role: "user" | "assistant"; content: string };

const KARSELEMLER = [
  "Kelam ilmi nedir?",
  "Namazın şartları nelerdir?",
  "Bismillahirrahmanirrahim anlamı nedir?",
  "Iman ile amel ilişkisi nasıl olur?",
];

export default function Chat() {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [bolum, setBolum] = useState("kelam");
  const [err, setErr] = useState("");
  const endRef = useRef<HTMLDivElement>(null);
  const recogRef = useRef<any>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs, loading]);

  const speak = useCallback((text: string) => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "tr-TR";
    u.onstart = () => setSpeaking(true);
    u.onend = () => setSpeaking(false);
    window.speechSynthesis.speak(u);
  }, []);

  const send = useCallback(
    async (text: string) => {
      const content = text.trim();
      if (!content || loading) return;
      setErr("");
      const gecmis = msgs.slice(-10);
      setMsgs((m) => [...m, { role: "user", content }, { role: "assistant", content: "" }]);
      setInput("");
      setLoading(true);
      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: content, bolum, history: gecmis }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Bir hata oluştu.");
        setMsgs((m) => {
          const c = [...m];
          c[c.length - 1] = { role: "assistant", content: data.reply };
          return c;
        });
        speak(data.reply);
      } catch (e: any) {
        setErr(e.message);
        setMsgs((m) => m.slice(0, -1));
      } finally {
        setLoading(false);
      }
    },
    [msgs, loading, bolum, speak]
  );

  const toggleListen = useCallback(() => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) {
      setErr("Bu tarayıcı ses tanımayı desteklemiyor (Chrome/Edge deneyin).");
      return;
    }
    if (listening) {
      recogRef.current?.stop();
      setListening(false);
      return;
    }
    const r = new SR();
    r.lang = "tr-TR";
    r.continuous = false;
    r.interimResults = true;
    r.onresult = (e: any) => {
      const t = Array.from(e.results).map((x: any) => x[0].transcript).join("");
      setInput(t);
      if (e.results[e.results.length - 1].isFinal) {
        setListening(false);
        send(t);
      }
    };
    r.onerror = () => { setListening(false); };
    r.onend = () => setListening(false);
    recogRef.current = r;
    r.start();
    setListening(true);
  }, [listening, send]);

  const stopSpeak = () => { window.speechSynthesis?.cancel(); setSpeaking(false); };

  return (
    <div className="chat-wrap">
      <header className="chat-header">
        <div className="logo">﴾ فقۂ ﴿ Faqih</div>
        <div className="hdr-right">
          <select value={bolum} onChange={(e) => setBolum(e.target.value)} aria-label="Bölüm seç">
            <option value="kelam">Kelam</option>
            <option value="idrak">İdrak</option>
            <option value="ameli">Ameli</option>
          </select>
          <button className="new-chat" onClick={() => { setMsgs([]); setErr(""); }}>+ Yeni sohbet</button>
        </div>
      </header>

      <div className="chat-body">
        {msgs.length === 0 ? (
          <div className="welcome">
            <h1>Bismillahirrahmanirrahim</h1>
            <p>Faqih'e sorun — kelam, idrak ve ameli bölümlerinde yardımcınız olur.</p>
            <div className="karselam">
              {KARSELEMLER.map((k) => (
                <button key={k} onClick={() => send(k)}>{k}</button>
              ))}
            </div>
          </div>
        ) : (
          msgs.map((m, i) => (
            <div key={i} className={`msg ${m.role}`}>
              <div className="avatar">{m.role === "user" ? "Sen" : "Fq"}</div>
              <div className="bubble">
                {m.role === "assistant" && m.content === "" && loading
                  ? <span className="dots"><span>.</span><span>.</span><span>.</span></span>
                  : m.content}
              </div>
            </div>
          ))
        )}
        <div ref={endRef} />
      </div>

      {err && <div className="err">⚠ {err}</div>}

      <footer className="chat-footer">
        <textarea
          value={input}
          placeholder={listening ? "Dinliyorum..." : "Faqih'e sorun... (Enter ile gönder)"}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input); }
          }}
          rows={1}
        />
        <button className={`mic ${listening ? "on" : ""}`} onClick={toggleListen} aria-label="Ses tanıma">
          {listening ? "⏺" : "🎤"}
        </button>
        {speaking
          ? <button className="send stop" onClick={stopSpeak} aria-label="Durdur">⏹</button>
          : <button className="send" onClick={() => send(input)} disabled={loading || !input.trim()} aria-label="Gönder">➤</button>}
      </footer>
      <div className="disclaimer">Faqih verdiği yanıtları teyid etmeniz için kaynaklara havale eder. İlim ehline danışınız.</div>
    </div>
  );
}
