import type { Metadata } from "next";
import { Lexend } from "next/font/google";
import PlausibleProvider from "next-plausible";
import { GoogleAnalytics } from '@next/third-parties/google'
import "./globals.css";

const inter = Lexend({ subsets: ["latin"] });

let title = "ResearchWizard | Powered by th3w1zard1";
let description = "Your intelligent AI research assistant that turns complex topics into clear insights. Receive thorough reports with verified references, professional layout, and personalized content—all accomplished with just one click.";
let url = "https://github.com/th3w1zard1";
let ogimage = "/wizard-icon-new.svg";
let sitename = "ResearchWizard";

export const metadata: Metadata = {
  metadataBase: new URL(url),
  title,
  description,
  icons: {
    icon: "/wizard-icon-new.svg",
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

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html className="gptr-root" lang="en">
      <head>
        {/* Font Awesome Icons */}
        <link
          rel="stylesheet"
          href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css"
          integrity="sha512-DTOQO9RWCH3ppGqcWaEA1BIZOC6xxalwEsw9c2QQeAIftl+Vegovlnee1c9QX4TctnWMn13TZye+giMm8e2LwA=="
          crossOrigin="anonymous"
          referrerPolicy="no-referrer"
        />
        <PlausibleProvider domain="localhost:3000" />
        <GoogleAnalytics gaId={process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID || ''} />
      </head>
      <body
        className={`app-container ${inter.className} flex min-h-screen flex-col justify-between`}
        suppressHydrationWarning
      >
        {/* Wizard background */}
        {/*<div
          className="fixed inset-0 z-[-1] opacity-40"
          style={{
            backgroundImage: 'url("/powerful_wizard.png")',
            backgroundPosition: 'center',
            backgroundSize: 'contain',
            backgroundRepeat: 'no-repeat',
            backgroundAttachment: 'fixed'
          }}
        />*/}
        {children}
      </body>
    </html>
  );
}
