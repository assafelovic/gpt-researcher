import type { Metadata, Viewport } from 'next';
import { Gelasio, Instrument_Sans, JetBrains_Mono } from 'next/font/google';
import { SettingsDialog } from './_components/Settings';
import { TopBar } from './_components/ui';
import './gr.css';

const display = Gelasio({ subsets: ['latin'], weight: ['400', '500', '600'], variable: '--font-display', display: 'swap' });
const body = Instrument_Sans({ subsets: ['latin'], variable: '--font-body', display: 'swap' });
const code = JetBrains_Mono({ subsets: ['latin'], variable: '--font-code', display: 'swap' });

export const metadata: Metadata = {
  title: 'GPT Researcher',
};

export const viewport: Viewport = {
  themeColor: '#EEE7D8',
};

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className={`gr ${display.variable} ${body.variable} ${code.variable} min-h-screen w-full bg-paper font-body text-ink`}>
      <div className="gr-grain" aria-hidden="true" />
      <TopBar />
      {children}
      <SettingsDialog />
    </div>
  );
}
