import './globals.css';
import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import { QueryProvider } from '../components/providers/query-provider';

export const metadata: Metadata = {
  title: 'Credara Enterprise',
  description: 'SME trade finance infrastructure on Polygon',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
