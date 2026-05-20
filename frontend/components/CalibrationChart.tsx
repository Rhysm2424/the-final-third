'use client';

import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { CalibrationBin } from '@/lib/types';

interface CalibrationChartProps {
  bins: CalibrationBin[];
}

export function CalibrationChart({ bins }: CalibrationChartProps) {
  const data = bins.map((b) => ({
    predicted: Math.round(b.predicted * 100),
    actual: Math.round(b.actual * 100),
    count: b.count,
  }));
  const perfect = [
    { predicted: 0, actual: 0 },
    { predicted: 100, actual: 100 },
  ];

  return (
    <div className="h-[280px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={data}
          margin={{ top: 12, right: 16, left: 0, bottom: 28 }}
        >
          <CartesianGrid stroke="#E6E0D3" strokeDasharray="2 3" />
          <XAxis
            type="number"
            dataKey="predicted"
            domain={[0, 100]}
            ticks={[0, 25, 50, 75, 100]}
            tick={{ fontFamily: 'JetBrains Mono', fontSize: 10, fill: '#8A8580' }}
            label={{
              value: 'PREDICTED PROBABILITY (%)',
              position: 'insideBottom',
              offset: -16,
              style: {
                fontFamily: 'JetBrains Mono',
                fontSize: 10,
                letterSpacing: '0.12em',
                fill: '#8A8580',
              },
            }}
          />
          <YAxis
            type="number"
            domain={[0, 100]}
            ticks={[0, 25, 50, 75, 100]}
            tick={{ fontFamily: 'JetBrains Mono', fontSize: 10, fill: '#8A8580' }}
            label={{
              value: 'ACTUAL RATE (%)',
              angle: -90,
              position: 'insideLeft',
              style: {
                fontFamily: 'JetBrains Mono',
                fontSize: 10,
                letterSpacing: '0.12em',
                fill: '#8A8580',
              },
            }}
          />
          <Tooltip
            contentStyle={{
              background: '#FFFFFF',
              border: '1px solid #E6E0D3',
              borderRadius: 4,
              fontFamily: 'Inter Tight',
              fontSize: 12,
            }}
            formatter={(value: number, name: string) => [`${value}%`, name]}
          />
          <Line
            type="linear"
            data={perfect}
            dataKey="actual"
            stroke="#8A8580"
            strokeDasharray="4 4"
            dot={false}
            isAnimationActive={false}
            name="Perfect"
          />
          <Line
            type="monotone"
            dataKey="actual"
            stroke="#034694"
            strokeWidth={2.5}
            dot={{ fill: '#034694', r: 4 }}
            activeDot={{ r: 6 }}
            isAnimationActive
            animationDuration={900}
            name="Model"
          />
          <ReferenceLine x={50} stroke="#E6E0D3" strokeDasharray="2 2" />
          <ReferenceLine y={50} stroke="#E6E0D3" strokeDasharray="2 2" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
