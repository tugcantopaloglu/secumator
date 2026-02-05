'use client';

import Link from 'next/link';
import { formatDistanceToNow, parseISO } from 'date-fns';
import { clsx } from 'clsx';
import { ArrowRight, ExternalLink } from 'lucide-react';

interface RecentScansProps {
  scans?: {
    id: number;
    target: string;
    status: string;
    scan_type: string;
    created_at: string;
  }[];
  loading?: boolean;
}

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  running: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  completed: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  failed: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  cancelled: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
};

export function RecentScans({ scans, loading }: RecentScansProps) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow">
      <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Recent Scans
        </h3>
        <Link
          href="/scans"
          className="text-primary-600 hover:text-primary-700 text-sm font-medium flex items-center"
        >
          View all
          <ArrowRight className="w-4 h-4 ml-1" />
        </Link>
      </div>
      <div className="divide-y divide-gray-200 dark:divide-gray-700">
        {loading ? (
          [...Array(5)].map((_, i) => (
            <div key={i} className="p-4 animate-pulse">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2" />
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
            </div>
          ))
        ) : scans?.length === 0 ? (
          <div className="p-6 text-center text-gray-500">No recent scans</div>
        ) : (
          scans?.map((scan) => (
            <Link
              key={scan.id}
              href={`/scans/${scan.id}`}
              className="block p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {scan.target}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <span
                      className={clsx(
                        'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
                        statusColors[scan.status]
                      )}
                    >
                      {scan.status}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {scan.scan_type}
                    </span>
                    <span className="text-xs text-gray-400">•</span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {formatDistanceToNow(parseISO(scan.created_at), {
                        addSuffix: true,
                      })}
                    </span>
                  </div>
                </div>
                <ExternalLink className="w-4 h-4 text-gray-400" />
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
