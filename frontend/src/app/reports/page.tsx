'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { FileText, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { formatDistanceToNow, parseISO } from 'date-fns';

export default function ReportsPage() {
  const { data: scans, isLoading } = useQuery({
    queryKey: ['completed-scans'],
    queryFn: () => api.getScans(1, 50),
  });

  const completedScans = scans?.items?.filter((s: any) => s.status === 'completed') || [];

  const handleExport = async (scanId: number, format: string) => {
    try {
      const blob = await api.exportReport(scanId.toString(), format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report-${scanId}.${format}`;
      a.click();
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Reports</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Download and manage security scan reports
        </p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl shadow overflow-hidden">
        {isLoading ? (
          <div className="animate-pulse p-6">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="py-4 border-b border-gray-200 dark:border-gray-700">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2" />
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
              </div>
            ))}
          </div>
        ) : completedScans.length === 0 ? (
          <div className="p-12 text-center text-gray-500">
            No completed scans with reports available
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {completedScans.map((scan: any) => (
              <div
                key={scan.id}
                className="p-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700/50"
              >
                <div className="flex items-center">
                  <FileText className="w-8 h-8 text-gray-400 mr-4" />
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {scan.target}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {scan.findings_count} findings •{' '}
                      {formatDistanceToNow(parseISO(scan.created_at), { addSuffix: true })}
                    </p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleExport(scan.id, 'pdf')}
                  >
                    <Download className="w-4 h-4 mr-1" />
                    PDF
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleExport(scan.id, 'html')}
                  >
                    <Download className="w-4 h-4 mr-1" />
                    HTML
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleExport(scan.id, 'sarif')}
                  >
                    <Download className="w-4 h-4 mr-1" />
                    SARIF
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
