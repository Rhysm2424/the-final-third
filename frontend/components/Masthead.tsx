'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';

const NAV = [
  { href: '/', label: 'Fixtures' },
  { href: '/insights', label: 'Insights' },
  { href: '/league', label: 'League' },
  { href: '/track-record', label: 'Track Record' },
];

export function Masthead() {
  const pathname = usePathname();
  const today = new Date()
    .toLocaleDateString('en-GB', {
      weekday: 'short',
      day: 'numeric',
      month: 'long',
      timeZone: 'UTC',
    })
    .toUpperCase();

  return (
    <header className="sticky top-0 z-50 backdrop-blur supports-[backdrop-filter]:bg-navy/95 bg-navy">
      <div className="container-narrow flex items-center justify-between gap-4 py-3.5">
        <Link href="/" className="group flex items-baseline gap-2.5">
          <span className="grid h-7 w-7 place-items-center rounded-sm bg-signal-gold font-serif text-base font-bold leading-none text-navy">
            ⅓
          </span>
          <span className="display-serif text-xl text-cream sm:text-2xl">
            The Final<span className="text-signal-gold">.</span>Third
          </span>
        </Link>
        <span className="hidden font-mono text-[10px] uppercase tracking-[0.15em] text-cream/55 sm:inline">
          {today}
        </span>
      </div>
      <nav className="container-narrow scrollbar-hide flex gap-0 overflow-x-auto border-t border-cream/10">
        {NAV.map((item) => {
          const active =
            item.href === '/' ? pathname === '/' : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'relative border-b-2 px-4 py-3 font-sans text-[11px] font-semibold uppercase tracking-[0.12em] transition-colors',
                active
                  ? 'border-signal-gold text-cream'
                  : 'border-transparent text-cream/55 hover:text-cream'
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </header>
  );
}
