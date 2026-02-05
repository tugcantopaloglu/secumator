'use client';

import { Scan, AlertTriangle, Shield, Calendar } from 'lucide-react';
import { clsx } from 'clsx';

interface StatsCardsProps {
  stats?: {
    total_scans: number;
    scans_this_week: number;
    scans_this_month: number;
    total_findings: number;
  };
  loading?: boolean;
}

export function StatsCards({ stats, loading }: StatsCardsProps) {
  const cards = [
    {
      name: 'Total Scans',
      value: stats?.total_scans || 0,
      icon: Scan,
      color: 'bg-blue-500',
      change: '+12%',
    },
    {
      name: 'This Week',
      value: stats?.scans_this_week || 0,
      icon: Calendar,
      color: 'bg-green-500',
      change: '+8%',
    },
    {
      name: 'This Month',
      value: stats?.scans_this_month || 0,
      icon: Shield,
      color: 'bg-purple-500',
      change: '+23%',
    },
    {
      name: 'Total Findings',
      value: stats?.total_findings || 0,
      icon: AlertTriangle,
      color: 'bg-orange-500',
      change: '-5%',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {cards.map((card) => (
        <div
          key={card.name}
          className={clsx(
            'bg-white dark:bg-gray-800 rounded-xl shadow p-6',
            loading && 'animate-pulse'
          )}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                {card.name}
              </p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
                {loading ? '-' : card.value.toLocaleString()}
              </p>
            </div>
            <div className={clsx('p-3 rounded-lg', card.color)}>
              <card.icon className="w-6 h-6 text-white" />
            </div>
          </div>
          <div className="mt-4 flex items-center">
            <span
              className={clsx(
                'text-sm font-medium',
                card.change.startsWith('+')
                  ? 'text-green-600'
                  : 'text-red-600'
              )}
            >
              {card.change}
            </span>
            <span className="text-sm text-gray-500 dark:text-gray-400 ml-2">
              vs last period
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
