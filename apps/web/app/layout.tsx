import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = { title: 'Credara Enterprise', description: 'SME trade finance infrastructure on Polygon' };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>{children}</body></html>;
}
