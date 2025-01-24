import type { Metadata } from "next";
import { Lexend } from "next/font/google";
import PlausibleProvider from "next-plausible";
import "./globals.css";

const inter = Lexend({ subsets: ["latin"] });

let title = "Content Spells AI Researcher";

let ogimage = "/favicon.ico";
let sitename = "Content Spells AI Researcher";

export const metadata: Metadata = {
  metadataBase: new URL("https://localhost:3000"),
  title,

  icons: {
    icon: "/favicon.ico",
  },
  openGraph: {
    images: [ogimage],
    title,

    siteName: sitename,
    locale: "en_US",
    type: "website",
  },

};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <PlausibleProvider domain="localhost:3000" />
      </head>
      <body
        className={`${inter.className} flex min-h-screen flex-col justify-between`}
      >
        {children}
      </body>
    </html>
  );
}
