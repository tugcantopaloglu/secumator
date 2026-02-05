'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Search, Filter, RefreshCw } from 'lucide-react';
import { api } from '@/lib/api';
import { ScanTable } from '@/components/scans/scan-table';
import { NewScanModal } from '@/components/scans/new-scan-modal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';

export default function ScansPage() {
  const [isNewScanOpen, setIsNewScanOpen] = useState(false);
  const [search, setSearch] = useState('');
  const queryClient = useQueryClient();

  const { data: scans, isLoading, refetch } = useQuery({
    queryKey: ['scans'],
    queryFn: () => api.getScans(),
    refetchInterval: 5000,
  });

  const createScan = useMutation({
    mutationFn: api.createScan,
    onSuccess: () => {
      toast.success('Scan started successfully');
      queryClient.invalidateQueries({ queryKey: ['scans'] });
      setIsNewScanOpen(false);
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to start scan');
    },
  });

  const filteredScans = scans?.items?.filter((scan: any) =>
    scan.target.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Scans</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage and monitor security scans
          </p>
        </div>
        <Button onClick={() => setIsNewScanOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          New Scan
        </Button>
      </div>

      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <Input
            placeholder="Search scans..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button variant="outline" onClick={() => refetch()}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      <ScanTable scans={filteredScans} loading={isLoading} />

      <NewScanModal
        open={isNewScanOpen}
        onClose={() => setIsNewScanOpen(false)}
        onSubmit={(data) => createScan.mutate(data)}
        loading={createScan.isPending}
      />
    </div>
  );
}
