import { api } from '@/lib/api';
import { PageHeader } from '@/components/PageHeader';
import { InsightCard } from '@/components/InsightCard';
import type { Insight } from '@/lib/types';

export const revalidate = 0;

export default async function InsightsPage() {
  let insights: Insight[] = [];
  try {
    insights = await api.insights(30);
  } catch {
    // handled below
  }

  return (
    <div>
      <PageHeader
        kicker="Pattern Mining"
        title="Things the numbers noticed."
        dek="Auto-surfaced patterns from the database, ranked by statistical notability. We only show signals strong enough that the data alone justifies the claim."
      />

      {insights.length === 0 ? (
        <div className="surface p-8 text-center text-sm text-ink/55">
          No insights surfaced yet.
        </div>
      ) : (
        insights.map((i, idx) => <InsightCard key={i.id} insight={i} index={idx} />)
      )}
    </div>
  );
}
