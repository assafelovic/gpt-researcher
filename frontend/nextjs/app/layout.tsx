import type { Metadata, Viewport } from "next";
import { Lexend } from "next/font/google";
import PlausibleProvider from "next-plausible";
import { GoogleAnalytics } from '@next/third-parties/google'
import { ResearchHistoryProvider } from "@/hooks/ResearchHistoryContext";
import "./globals.css";
import Script from 'next/script';
import { hltBranding } from "@/lib/hltBranding";

const inter = Lexend({ subsets: ["latin"] });

let title = hltBranding.enabled ? `${hltBranding.productName} | ${hltBranding.ownerName}` : "GPT Researcher";
let description = hltBranding.enabled
  ? "HLT research workspace powered by GPT Researcher for source-backed web and local research."
  : "LLM based autonomous agent that conducts local and web research on any topic and generates a comprehensive report with citations.";
let url = hltBranding.enabled ? hltBranding.uiUrl : "https://github.com/assafelovic/gpt-researcher";
let ogimage = hltBranding.enabled ? hltBranding.icon : "/favicon.ico";
let sitename = hltBranding.enabled ? hltBranding.productName : "GPT Researcher";

export const metadata: Metadata = {
  metadataBase: new URL(url),
  title,
  description,
  manifest: '/manifest.json',
  icons: {
    icon: hltBranding.enabled ? hltBranding.icon : "/img/gptr-black-logo.png",
    apple: hltBranding.enabled ? hltBranding.icon : '/img/gptr-black-logo.png',
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: title,
  },
  openGraph: {
    images: [ogimage],
    title,
    description,
    url: url,
    siteName: sitename,
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    images: [ogimage],
    title,
    description,
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: hltBranding.enabled ? hltBranding.deepNavy : '#111827',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {

  return (
    <html className="gptr-root" lang="en" suppressHydrationWarning>
      <head>
        <PlausibleProvider domain="localhost:3000" />
        <GoogleAnalytics gaId={process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID!} />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <link rel="apple-touch-icon" href={hltBranding.enabled ? hltBranding.icon : "/img/gptr-black-logo.png"} />
      </head>
      <body
        className={`app-container ${inter.className} flex min-h-screen flex-col justify-between`}
        suppressHydrationWarning
      >
        <ResearchHistoryProvider>
          {children}
        </ResearchHistoryProvider>
      </body>
    </html>
  );
}
