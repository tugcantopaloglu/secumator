'use client';

import Link from 'next/link';
import { formatDistanceToNow, parseISO } from 'date-fns';
import { clsx } from 'clsx';
import { ExternalLink, MoreVertical, Play, Square, Trash } from 'lucide-react';

interface Scan {
  id: number;
  target: string;
  status: string;
  scan_type: string;
  profile?: string;
  findings_count: number;
  created_at: string;
  completed_at?: string;
}

interface ScanTableProps {
  scans?: Scan[];
  loading?: boolean;
}

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  running: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  completed: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  failed: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  cancelled: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
};

export function ScanTable({ scans, loading }: ScanTableProps) {
  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow overflow-hidden">
        <div className="animate-pulse">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className="p-4 border-b border-gray-200 dark:border-gray-700"
            >
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2" />
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!scans?.length) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-12 text-center">
        <p className="text-gray-500 dark:text-gray-400">
          No scans found. Start a new scan to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-900">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Target
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Findings
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Created
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {scans.map((scan) => (
              <tr
                key={scan.id}
                className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  <Link
                    href={`/scans/${scan.id}`}
                    className="text-sm font-medium text-primary-600 hover:text-primary-700 truncate max-w-xs block"
                  >
                    {scan.target}
                  </Link>
                  {scan.profile && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Profile: {scan.profile}
                    </p>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={clsx(
                      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                      statusColors[scan.status]
                    )}
                  >
                    {scan.status === 'running' && (
                      <span className="w-2 h-2 bg-current rounded-full animate-pulse mr-1.5" />
                    )}
                    {scan.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  {scan.scan_type}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {scan.findings_count}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  {formatDistanceToNow(parseISO(scan.created_at), {
                    addSuffix: true,
                  })}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right">
                  <Link
                    href={`/scans/${scan.id}`}
                    className="text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
                  >
                    <ExternalLink className="w-5 h-5" />
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
