'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { TrendsChart } from '@/components/dashboard/trends-chart';
import { SeverityChart } from '@/components/dashboard/severity-chart';
import { Select } from '@/components/ui/select';
import { useState } from 'react';

export default function AnalyticsPage() {
  const [period, setPeriod] = useState('30');

  const { data: stats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: api.getStats,
  });

  const { data: trends, isLoading: trendsLoading } = useQuery({
    queryKey: ['trends', period],
    queryFn: () => api.getTrends(parseInt(period)),
  });

  const { data: topVulns } = useQuery({
    queryKey: ['top-vulnerabilities'],
    queryFn: api.getTopVulnerabilities,
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Analytics
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Security trends and insights
          </p>
        </div>
        <Select
          options={[
            { value: '7', label: 'Last 7 days' },
            { value: '30', label: 'Last 30 days' },
            { value: '90', label: 'Last 90 days' },
          ]}
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TrendsChart data={trends} loading={trendsLoading} />
        <SeverityChart data={stats?.severity_distribution} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Top Vulnerability Types
          </h3>
          <div className="space-y-4">
            {topVulns?.top_vulnerabilities?.slice(0, 10).map((vuln: any, i: number) => (
              <div key={i} className="flex items-center">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {vuln.title}
                  </p>
                  <div className="mt-1 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-primary-500 h-2 rounded-full"
                      style={{
                        width: `${(vuln.count / (topVulns.top_vulnerabilities[0]?.count || 1)) * 100}%`,
                      }}
                    />
                  </div>
                </div>
                <span className="ml-4 text-sm font-medium text-gray-500">
                  {vuln.count}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Severity Over Time
          </h3>
          <div className="space-y-4">
            {trends?.severity_trend?.map((item: any) => (
              <div key={item.severity} className="flex items-center justify-between">
                <div className="flex items-center">
                  <div
                    className="w-3 h-3 rounded-full mr-3"
                    style={{
                      backgroundColor:
                        item.severity === 'critical'
                          ? '#ef4444'
                          : item.severity === 'high'
                          ? '#f97316'
                          : item.severity === 'medium'
                          ? '#eab308'
                          : '#22c55e',
                    }}
                  />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300 capitalize">
                    {item.severity}
                  </span>
                </div>
                <span className="text-lg font-bold text-gray-900 dark:text-white">
                  {item.count}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
