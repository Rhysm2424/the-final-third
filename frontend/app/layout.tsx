import type { Metadata } from 'next';
import '@/styles/globals.css';
import { Masthead } from '@/components/Masthead';
import { DemoBanner } from '@/components/DemoBanner';

export const metadata: Metadata = {
  title: 'The Final Third — Football, modelled.',
  description:
    'Probabilistic football match forecasts, calibration-tracked predictions, and data-driven insights.',
  metadataBase: new URL('https://thefinalthird.com'),
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="bg-cream">
      <body className="min-h-screen">
        <DemoBanner />
        <Masthead />
        <main className="container-narrow py-8 sm:py-12">{children}</main>
        <footer className="border-t border-line bg-cream-50 py-10">
          <div className="container-narrow text-xs text-ink/50">
            <p className="mb-1 font-serif italic">The Final Third — statistical match analysis</p>
            <p>
              Predictions are framed as statistical analysis, not betting tips. Calibration data
              is shown in the Track Record page. All references to bookmaker odds are for
              benchmarking only.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
