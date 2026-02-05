'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { format, parseISO } from 'date-fns';

interface TrendsChartProps {
  data?: {
    scans_by_day: { date: string; count: number }[];
    findings_by_day: { date: string; count: number }[];
    period_days: number;
  };
  loading?: boolean;
}

export function TrendsChart({ data, loading }: TrendsChartProps) {
  const chartData = data?.scans_by_day?.map((scan, index) => ({
    date: scan.date,
    scans: scan.count,
    findings: data.findings_by_day?.[index]?.count || 0,
  })) || [];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Activity Trends (Last {data?.period_days || 30} Days)
      </h3>
      {loading ? (
        <div className="h-64 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
        </div>
      ) : (
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis
                dataKey="date"
                tickFormatter={(value) => format(parseISO(value), 'MMM d')}
                tick={{ fill: '#9ca3af', fontSize: 12 }}
                tickLine={false}
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fill: '#9ca3af', fontSize: 12 }}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--tooltip-bg, #fff)',
                  border: 'none',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                }}
                labelFormatter={(value) => format(parseISO(value), 'MMM d, yyyy')}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="scans"
                stroke="#0ea5e9"
                strokeWidth={2}
                dot={false}
                name="Scans"
              />
              <Line
                type="monotone"
                dataKey="findings"
                stroke="#f97316"
                strokeWidth={2}
                dot={false}
                name="Findings"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
