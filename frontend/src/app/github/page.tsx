'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { GitBranch, Search, Scan } from 'lucide-react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { toast } from 'sonner';

export default function GitHubPage() {
  const [repoUrl, setRepoUrl] = useState('');
  const [branch, setBranch] = useState('main');
  const [scanType, setScanType] = useState('webapp');
  const queryClient = useQueryClient();

  const scanRepo = useMutation({
    mutationFn: api.scanGitHubRepo,
    onSuccess: () => {
      toast.success('GitHub scan started');
      queryClient.invalidateQueries({ queryKey: ['scans'] });
      setRepoUrl('');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to start scan');
    },
  });

  const handleScan = () => {
    if (!repoUrl) return;
    scanRepo.mutate({ repo_url: repoUrl, branch, scan_type: scanType });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          GitHub Integration
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Scan GitHub repositories for security vulnerabilities
        </p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Scan Repository
        </h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Repository URL
            </label>
            <div className="flex gap-4">
              <div className="flex-1 relative">
                <GitBranch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <Input
                  placeholder="https://github.com/owner/repo"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Branch
              </label>
              <Input
                placeholder="main"
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Scan Type
              </label>
              <Select
                options={[
                  { value: 'webapp', label: 'Web Application' },
                  { value: 'api', label: 'API' },
                  { value: 'full', label: 'Full Security' },
                ]}
                value={scanType}
                onChange={(e) => setScanType(e.target.value)}
              />
            </div>
          </div>

          <Button
            onClick={handleScan}
            disabled={!repoUrl || scanRepo.isPending}
            className="w-full"
          >
            <Scan className="w-4 h-4 mr-2" />
            {scanRepo.isPending ? 'Starting Scan...' : 'Start Security Scan'}
          </Button>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          GitHub Actions Integration
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Add this workflow to your repository to automatically scan on pull requests:
        </p>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
{`name: Security Scan
on:
  pull_request:
    branches: [main]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Secumator Scan
        env:
          SECUMATOR_API_URL: \${{ secrets.SECUMATOR_API_URL }}
          GITHUB_TOKEN: \${{ secrets.GITHUB_TOKEN }}
        run: |
          curl -X POST "\$SECUMATOR_API_URL/api/v1/github/scan" \\
            -H "Content-Type: application/json" \\
            -d '{"repo_url": "\${{ github.repository }}", "branch": "\${{ github.head_ref }}"}'
      
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: results.sarif`}
        </pre>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Webhook Setup
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Configure a webhook in your GitHub repository settings to automatically trigger scans:
        </p>
        <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
          <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Webhook URL</p>
          <code className="text-sm text-primary-600 dark:text-primary-400">
            {process.env.NEXT_PUBLIC_API_URL || 'https://your-secumator-instance'}/api/v1/github/webhook
          </code>
          <p className="text-xs text-gray-500 mt-2">
            Events: Pull requests (opened, synchronize)
          </p>
        </div>
      </div>
    </div>
  );
}
