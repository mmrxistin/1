import { NextResponse } from "next/server";

// AQL Python motoru (Faqih-ai/aql) ile haberlesen API koprusu.
// Motor: uvicorn ile `python -m aql.api` seklinde 127.0.0.1:8000'de calisir.
const AQL_URL = process.env.AQL_URL || "http://127.0.0.1:8000";

export async function POST(req: Request) {
  let mesaj = "", bolum = "kelam";
  try {
    const body = await req.json();
    mesaj = String(body.mesaj || "").trim();
    bolum = String(body.bolum || "kelam");
  } catch {
    return NextResponse.json({ error: "Gecersiz istek govdesi." }, { status: 400 });
  }
  if (!mesaj) {
    return NextResponse.json({ error: "Soru bos olamaz." }, { status: 400 });
  }
  try {
    const res = await fetch(`${AQL_URL}/sor`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bolum, soru: mesaj }),
      signal: AbortSignal.timeout(30000),
    });
    if (!res.ok) {
      const hata = await res.json().catch(() => ({}));
      return NextResponse.json(
        { error: hata.error || `AQL motoru hata dondu (${res.status}).` },
        { status: 502 }
      );
    }
    const data = await res.json();
    return NextResponse.json({ cevap: String(data.cevap || "") });
  } catch {
    return NextResponse.json(
      { error: "AQL motoruna baglanilamadi. Motoru baslatin: python -m aql.api" },
      { status: 502 }
    );
  }
}
