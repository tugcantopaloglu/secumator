'use client';

import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts';

interface SeverityChartProps {
  data?: Record<string, number>;
  loading?: boolean;
  compact?: boolean;
}

const COLORS: Record<string, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
  info: '#3b82f6',
};

export function SeverityChart({ data, loading, compact }: SeverityChartProps) {
  const chartData = data
    ? Object.entries(data)
        .filter(([_, value]) => value > 0)
        .map(([key, value]) => ({
          name: key.charAt(0).toUpperCase() + key.slice(1),
          value,
          color: COLORS[key],
        }))
    : [];

  const total = chartData.reduce((acc, item) => acc + item.value, 0);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Severity Distribution
      </h3>
      {loading ? (
        <div className="h-64 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
        </div>
      ) : total === 0 ? (
        <div className="h-64 flex items-center justify-center text-gray-500">
          No findings data
        </div>
      ) : (
        <div className={compact ? 'h-48' : 'h-64'}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={compact ? 40 : 60}
                outerRadius={compact ? 70 : 90}
                paddingAngle={2}
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--tooltip-bg, #fff)',
                  border: 'none',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                }}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}
      <div className="grid grid-cols-5 gap-2 mt-4">
        {Object.entries(COLORS).map(([severity, color]) => (
          <div key={severity} className="text-center">
            <div
              className="w-3 h-3 rounded-full mx-auto mb-1"
              style={{ backgroundColor: color }}
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">
              {severity}
            </p>
            <p className="text-sm font-semibold text-gray-900 dark:text-white">
              {data?.[severity] || 0}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
