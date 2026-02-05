'use client';

import { useQuery } from '@tanstack/react-query';
import { StatsCards } from '@/components/dashboard/stats-cards';
import { SeverityChart } from '@/components/dashboard/severity-chart';
import { TrendsChart } from '@/components/dashboard/trends-chart';
import { RecentScans } from '@/components/dashboard/recent-scans';
import { TopVulnerabilities } from '@/components/dashboard/top-vulnerabilities';
import { api } from '@/lib/api';

export default function DashboardPage() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => api.getStats(),
  });

  const { data: trends, isLoading: trendsLoading } = useQuery({
    queryKey: ['trends'],
    queryFn: () => api.getTrends(30),
  });

  const { data: topVulns } = useQuery({
    queryKey: ['top-vulnerabilities'],
    queryFn: () => api.getTopVulnerabilities(),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Security Dashboard
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Overview of your security posture
        </p>
      </div>

      <StatsCards stats={stats?.overview} loading={statsLoading} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SeverityChart data={stats?.severity_distribution} loading={statsLoading} />
        <TrendsChart data={trends} loading={trendsLoading} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RecentScans scans={stats?.recent_scans} loading={statsLoading} />
        <TopVulnerabilities data={topVulns} />
      </div>
    </div>
  );
}
