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
  const today = new Date().toLocaleDateString('en-GB', {
    weekday: 'short',
    day: 'numeric',
    month: 'long',
  });

  return (
    <header className="sticky top-0 z-50 border-b border-line bg-cream/90 backdrop-blur supports-[backdrop-filter]:bg-cream/75">
      <div className="container-narrow flex items-baseline justify-between gap-4 pb-2 pt-3.5">
        <Link href="/" className="flex items-baseline gap-2">
          <span className="display-serif text-2xl italic">
            The Final<span className="text-navy">.</span>Third
          </span>
        </Link>
        <span className="label-mono hidden sm:inline">{today}</span>
      </div>
      <nav className="container-narrow scrollbar-hide flex gap-0 overflow-x-auto">
        {NAV.map((item) => {
          const active =
            item.href === '/' ? pathname === '/' : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'border-b-2 px-4 py-3 font-sans text-xs font-semibold uppercase tracking-wider transition-colors',
                active
                  ? 'border-navy text-ink'
                  : 'border-transparent text-ink/50 hover:text-ink'
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
