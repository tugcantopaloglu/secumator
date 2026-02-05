'use client';

import { useQuery } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import { useWebSocket } from '@/lib/websocket';
import { useState, useEffect } from 'react';
import { ScanProgress } from '@/components/scans/scan-progress';
import { FindingsTable } from '@/components/scans/findings-table';
import { ScanInfo } from '@/components/scans/scan-info';
import { SeverityChart } from '@/components/dashboard/severity-chart';
import { ArrowLeft, Download, FileText, Sparkles } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

export default function ScanDetailPage() {
  const params = useParams();
  const scanId = params.id as string;
  const { subscribe } = useWebSocket();
  const [progress, setProgress] = useState(0);
  const [liveFindings, setLiveFindings] = useState<any[]>([]);

  const { data: scan, isLoading, refetch } = useQuery({
    queryKey: ['scan', scanId],
    queryFn: () => api.getScan(scanId),
    refetchInterval: (query) =>
      query.state.data?.status === 'running' ? 2000 : false,
  });

  const { data: aiSummary, isLoading: aiLoading } = useQuery({
    queryKey: ['ai-summary', scanId],
    queryFn: () => api.getAISummary(scanId),
    enabled: scan?.status === 'completed',
  });

  useEffect(() => {
    const unsubscribe = subscribe(scanId, (message) => {
      if (message.type === 'scan_progress') {
        setProgress(message.progress);
      } else if (message.type === 'finding') {
        setLiveFindings((prev) => [...prev, message.finding]);
      } else if (message.type === 'scan_complete') {
        refetch();
        toast.success('Scan completed');
      }
    });

    return () => unsubscribe();
  }, [scanId, subscribe, refetch]);

  const handleExport = async (format: string) => {
    try {
      const blob = await api.exportReport(scanId, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `scan-${scanId}.${format}`;
      a.click();
      toast.success(`Exported as ${format.toUpperCase()}`);
    } catch (error) {
      toast.error('Export failed');
    }
  };

  const allFindings = [...(scan?.findings || []), ...liveFindings];
  const severityDistribution = allFindings.reduce(
    (acc: any, f: any) => {
      acc[f.severity] = (acc[f.severity] || 0) + 1;
      return acc;
    },
    {}
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/scans">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Scan Details
            </h1>
            <p className="text-gray-600 dark:text-gray-400">{scan?.target}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => handleExport('pdf')}>
            <FileText className="w-4 h-4 mr-2" />
            PDF
          </Button>
          <Button variant="outline" onClick={() => handleExport('sarif')}>
            <Download className="w-4 h-4 mr-2" />
            SARIF
          </Button>
        </div>
      </div>

      {scan?.status === 'running' && <ScanProgress progress={progress} />}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ScanInfo scan={scan} loading={isLoading} />
        </div>
        <div>
          <SeverityChart data={severityDistribution} loading={isLoading} compact />
        </div>
      </div>

      {aiSummary && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-5 h-5 text-purple-500" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              AI Risk Assessment
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-sm text-gray-500 dark:text-gray-400">Risk Score</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white">
                {aiSummary.risk_score}/100
              </p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-sm text-gray-500 dark:text-gray-400">Risk Level</p>
              <p className={`text-2xl font-bold ${
                aiSummary.risk_level === 'Critical' ? 'text-red-500' :
                aiSummary.risk_level === 'High' ? 'text-orange-500' :
                aiSummary.risk_level === 'Medium' ? 'text-yellow-500' : 'text-green-500'
              }`}>
                {aiSummary.risk_level}
              </p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-sm text-gray-500 dark:text-gray-400">Findings</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white">
                {aiSummary.findings_count}
              </p>
            </div>
          </div>
          <p className="text-gray-700 dark:text-gray-300">{aiSummary.executive_summary}</p>
        </div>
      )}

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Findings ({allFindings.length})
          </h2>
        </div>
        <FindingsTable findings={allFindings} loading={isLoading} />
      </div>
    </div>
  );
}
