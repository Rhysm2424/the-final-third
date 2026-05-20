import { api } from '@/lib/api';
import { PageHeader } from '@/components/PageHeader';
import { SectionLabel } from '@/components/SectionLabel';
import { CalibrationChart } from '@/components/CalibrationChart';
import { formatProb } from '@/lib/utils';

export const revalidate = 0;

export default async function TrackRecordPage() {
  let data;
  try {
    data = await api.trackRecord();
  } catch {
    data = null;
  }

  const s = data?.summary;

  return (
    <div>
      <PageHeader
        kicker="Receipts"
        title="Every prediction. Every result."
        dek="We keep score so you don't have to. All forecasts are logged at publication and never edited. Calibration is the test that matters: a 70% prediction should be right 70% of the time."
      />

      {!s || s.n_predictions === 0 ? (
        <div className="surface p-8 text-center text-sm text-ink/55">
          No backtest results yet. Run <code className="font-mono">make backtest</code> to
          populate.
        </div>
      ) : (
        <>
          <div className="mb-9 grid grid-cols-2 gap-px overflow-hidden rounded-md border border-line bg-line sm:grid-cols-4">
            <SummaryStat
              label="Predictions"
              value={s.n_predictions.toLocaleString()}
              sub={`${s.model_name} · seasons ${s.season_range}`}
            />
            <SummaryStat
              label="Brier Score"
              value={s.brier_score.toFixed(3)}
              sub={
                s.market_brier !== null
                  ? `lower is better · market ${s.market_brier.toFixed(3)}`
                  : 'lower is better'
              }
            />
            <SummaryStat
              label="Top-pick Accuracy"
              value={formatProb(s.top_pick_accuracy)}
              sub="vs random 33%"
            />
            <SummaryStat
              label="Log Loss"
              value={s.log_loss.toFixed(3)}
              sub={
                s.market_log_loss !== null
                  ? `market ${s.market_log_loss.toFixed(3)}`
                  : '—'
              }
            />
          </div>

          <div className="surface mb-9 px-7 py-7">
            <h2 className="display-serif mb-1 text-2xl">Calibration Curve</h2>
            <p className="mb-6 font-serif text-sm italic text-ink/60">
              How often the predicted probability matches the actual outcome rate. Points near the
              diagonal mean the model is well-calibrated.
            </p>
            <CalibrationChart bins={s.calibration_bins} />
          </div>

          {s.simulated_pnl_units !== null && s.simulated_roi_pct !== null && (
            <div className="surface mb-9 border-l-4 border-l-signal-gold px-7 py-6">
              <div className="label-mono mb-2 text-signal-red">For Research Only</div>
              <h3 className="display-serif mb-2 text-xl">Simulated Betting P&amp;L</h3>
              <p className="mb-4 max-w-prose font-serif text-sm leading-relaxed italic text-ink/70">
                A simulated flat-staking strategy applied to the model&rsquo;s value picks (where
                its probability exceeds the market&rsquo;s implied probability by 2pp or more)
                against closing odds. This is a model evaluation tool, not betting advice. Past
                results would not predict future results.
              </p>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="label-mono mb-1">P&amp;L (units)</div>
                  <div className="display-serif text-2xl">
                    {s.simulated_pnl_units >= 0 ? '+' : ''}
                    {s.simulated_pnl_units.toFixed(1)}
                  </div>
                </div>
                <div>
                  <div className="label-mono mb-1">ROI</div>
                  <div className="display-serif text-2xl">
                    {s.simulated_roi_pct >= 0 ? '+' : ''}
                    {s.simulated_roi_pct.toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>
          )}

          {data && data.recent.length > 0 && (
            <>
              <SectionLabel>Recent Predictions</SectionLabel>
              <div>
                {data.recent.map((row) => (
                  <div
                    key={row.match_id}
                    className="grid grid-cols-[60px_1fr_auto_auto] items-center gap-4 border-b border-line py-3"
                  >
                    <div className="font-mono text-[11px] text-ink/55">
                      {new Date(row.date).toLocaleDateString('en-GB', {
                        day: 'numeric',
                        month: 'short',
                      })}
                    </div>
                    <div>
                      <span className="font-serif text-base">
                        {row.home_team} v {row.away_team}
                      </span>
                      {row.home_score !== null && row.away_score !== null && (
                        <span className="ml-2 font-mono text-xs text-ink/55">
                          {row.home_score}–{row.away_score}
                        </span>
                      )}
                    </div>
                    <div className="font-mono text-xs text-ink/55">
                      {row.pick_label} {formatProb(row.pick_probability)}
                    </div>
                    <ResultPill result={row.result} />
                  </div>
                ))}
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}

function SummaryStat({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub: string;
}) {
  return (
    <div className="bg-paper px-5 py-5">
      <div className="label-mono mb-2">{label}</div>
      <div className="display-serif text-2xl leading-none">{value}</div>
      <div className="mt-1.5 font-mono text-[10px] text-ink/45">{sub}</div>
    </div>
  );
}

function ResultPill({ result }: { result: 'hit' | 'miss' | 'pending' }) {
  const map = {
    hit: 'bg-signal-green/15 text-signal-green',
    miss: 'bg-signal-red/15 text-signal-red',
    pending: 'bg-cream-200 text-ink/55',
  } as const;
  const label = { hit: 'Hit', miss: 'Miss', pending: '—' }[result];
  return (
    <span
      className={`rounded-sm px-2 py-1 font-mono text-[10px] font-semibold uppercase tracking-wider ${map[result]}`}
    >
      {label}
    </span>
  );
}
