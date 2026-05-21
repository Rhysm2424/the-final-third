import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatProb(p: number | null | undefined): string {
  if (p === null || p === undefined) return '—';
  return `${Math.round(p * 100)}%`;
}

export function formatXg(x: number | null | undefined): string {
  if (x === null || x === undefined) return '—';
  return x.toFixed(2);
}

// All date formatting locks the timezone to UTC so server-side and
// client-side renders match exactly (avoids hydration mismatches).
const TZ = 'UTC';

export function formatKickoff(iso: string): {
  weekday: string;
  date: string;
  time: string;
  full: string;
} {
  const d = new Date(iso);
  const weekday = d.toLocaleDateString('en-GB', { weekday: 'short', timeZone: TZ });
  const date = d.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    timeZone: TZ,
  });
  const time = d.toLocaleTimeString('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
    timeZone: TZ,
  });
  const full = `${weekday}, ${date} · ${time}`;
  return { weekday, date, time, full };
}

export function groupBy<T, K extends string | number>(
  arr: T[],
  key: (item: T) => K
): Record<K, T[]> {
  return arr.reduce(
    (acc, item) => {
      const k = key(item);
      if (!acc[k]) acc[k] = [];
      acc[k].push(item);
      return acc;
    },
    {} as Record<K, T[]>
  );
}
