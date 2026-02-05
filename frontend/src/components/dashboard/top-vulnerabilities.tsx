'use client';

import { AlertTriangle } from 'lucide-react';

interface TopVulnerabilitiesProps {
  data?: {
    top_vulnerabilities: { title: string; count: number }[];
    most_affected_components: { component: string; count: number }[];
  };
}

export function TopVulnerabilities({ data }: TopVulnerabilitiesProps) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow">
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Top Vulnerabilities
        </h3>
      </div>
      <div className="p-6">
        {data?.top_vulnerabilities?.length === 0 ? (
          <div className="text-center text-gray-500 py-4">
            No vulnerabilities found
          </div>
        ) : (
          <div className="space-y-4">
            {data?.top_vulnerabilities?.slice(0, 5).map((vuln, index) => (
              <div key={index} className="flex items-center">
                <div className="flex-shrink-0">
                  <AlertTriangle className="w-5 h-5 text-orange-500" />
                </div>
                <div className="ml-3 flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {vuln.title}
                  </p>
                </div>
                <div className="ml-3">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200">
                    {vuln.count}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}

        {data?.most_affected_components && data.most_affected_components.length > 0 && (
          <>
            <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
              <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-4">
                Most Affected Components
              </h4>
              <div className="space-y-3">
                {data.most_affected_components.slice(0, 5).map((comp, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <code className="text-xs text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded truncate max-w-[200px]">
                      {comp.component}
                    </code>
                    <span className="text-sm text-gray-500">{comp.count}</span>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
