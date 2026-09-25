import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const API_BASE = process.env.FAQIH_API_URL || "http://127.0.0.1:8000";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mesaj: body.message ?? body.mesaj ?? "",
        bolum: body.bolum ?? "kelam",
        gecmis: body.history ?? [],
      }),
    });
    if (!res.ok) {
      return NextResponse.json(
        { error: `API hatası: ${res.status}` },
        { status: 502 }
      );
    }
    const data = await res.json();
    return NextResponse.json({
      reply: data.cevap ?? data.reply ?? data.answer ?? "",
    });
  } catch (e) {
    return NextResponse.json(
      { error: "Faqih API sunucusuna ulaşılamadı." },
      { status: 502 }
    );
  }
}
