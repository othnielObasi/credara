import './globals.css';
import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import { QueryProvider } from '../components/providers/query-provider';

export const metadata: Metadata = {
  title: { default: 'Credara Enterprise', template: '%s · Credara' },
  description: 'SME trade finance infrastructure on Polygon',
  applicationName: 'Credara',
  authors: [{ name: 'Credara' }],
  openGraph: {
    title: 'Credara Enterprise',
    description: 'SME trade finance on Polygon — verified invoices, tokenized receivables, Smart LC settlement.',
    siteName: 'Credara',
  },
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
