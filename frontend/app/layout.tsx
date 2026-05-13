import type { Metadata } from "next";
import { Space_Grotesk } from "next/font/google";

import "./globals.css";

const bodyFont = Space_Grotesk({ subsets: ["latin"], variable: "--font-body" });

export const metadata: Metadata = {
  title: "ChatSUD",
  description: "Privacy-first therapeutic support for substance use recovery"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={bodyFont.variable}>{children}</body>
    </html>
  );
}
