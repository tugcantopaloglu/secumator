'use client';

import { Activity } from 'lucide-react';

interface ScanProgressProps {
  progress: number;
}

export function ScanProgress({ progress }: ScanProgressProps) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Activity className="w-5 h-5 text-primary-600 animate-pulse mr-2" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Scan in Progress
          </h3>
        </div>
        <span className="text-2xl font-bold text-primary-600">{progress}%</span>
      </div>
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
        <div
          className="bg-gradient-to-r from-primary-500 to-primary-600 h-full rounded-full transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>
      <p className="mt-3 text-sm text-gray-500 dark:text-gray-400">
        Scanning target for vulnerabilities...
      </p>
    </div>
  );
}
