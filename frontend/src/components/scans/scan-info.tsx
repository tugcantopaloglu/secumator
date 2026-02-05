'use client';

import { format, parseISO } from 'date-fns';
import { clsx } from 'clsx';
import {
  Globe,
  Clock,
  Calendar,
  Tag,
  Server,
  AlertCircle,
} from 'lucide-react';

interface ScanInfoProps {
  scan?: {
    id: number;
    target: string;
    status: string;
    scan_type: string;
    profile?: string;
    started_at?: string;
    completed_at?: string;
    error_message?: string;
    created_at: string;
  };
  loading?: boolean;
}

const statusColors: Record<string, string> = {
  pending: 'text-yellow-500',
  running: 'text-blue-500',
  completed: 'text-green-500',
  failed: 'text-red-500',
  cancelled: 'text-gray-500',
};

export function ScanInfo({ scan, loading }: ScanInfoProps) {
  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6 animate-pulse">
        <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-4" />
        <div className="space-y-3">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-2/3" />
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
        </div>
      </div>
    );
  }

  if (!scan) return null;

  const infoItems = [
    { icon: Globe, label: 'Target', value: scan.target },
    {
      icon: Tag,
      label: 'Status',
      value: scan.status,
      className: statusColors[scan.status],
    },
    { icon: Server, label: 'Scan Type', value: scan.scan_type },
    ...(scan.profile ? [{ icon: Tag, label: 'Profile', value: scan.profile }] : []),
    {
      icon: Calendar,
      label: 'Created',
      value: format(parseISO(scan.created_at), 'PPpp'),
    },
    ...(scan.started_at
      ? [
          {
            icon: Clock,
            label: 'Started',
            value: format(parseISO(scan.started_at), 'PPpp'),
          },
        ]
      : []),
    ...(scan.completed_at
      ? [
          {
            icon: Clock,
            label: 'Completed',
            value: format(parseISO(scan.completed_at), 'PPpp'),
          },
        ]
      : []),
  ];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Scan Information
      </h3>
      <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {infoItems.map((item, index) => (
          <div key={index} className="flex items-start">
            <item.icon className="w-5 h-5 text-gray-400 mr-3 mt-0.5" />
            <div>
              <dt className="text-sm text-gray-500 dark:text-gray-400">
                {item.label}
              </dt>
              <dd
                className={clsx(
                  'text-sm font-medium text-gray-900 dark:text-white mt-0.5 break-all',
                  item.className
                )}
              >
                {item.value}
              </dd>
            </div>
          </div>
        ))}
      </dl>

      {scan.error_message && (
        <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
          <div className="flex items-start">
            <AlertCircle className="w-5 h-5 text-red-500 mr-2 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-red-800 dark:text-red-200">
                Error
              </p>
              <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                {scan.error_message}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
