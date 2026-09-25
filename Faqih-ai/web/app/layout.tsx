import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Faqih AI",
  description: "Fikih sorulari icin deneysel yapay zeka arayuzu",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr">
      <body>{children}</body>
    </html>
  );
}
