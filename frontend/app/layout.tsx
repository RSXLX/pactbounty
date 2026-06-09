import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'PactBounty Demo',
  description: 'CAW-powered agent-to-agent Web3 audit bounty dashboard'
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
