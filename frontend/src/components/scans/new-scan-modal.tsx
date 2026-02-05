'use client';

import { useState } from 'react';
import { Modal } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Globe, Server, Code, Shield } from 'lucide-react';

interface NewScanModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: { target: string; scan_type: string; profile?: string }) => void;
  loading?: boolean;
}

const scanTypes = [
  { value: 'webapp', label: 'Web Application', icon: Globe },
  { value: 'network', label: 'Network', icon: Server },
  { value: 'api', label: 'API', icon: Code },
  { value: 'full', label: 'Full Security', icon: Shield },
];

const profiles = [
  { value: '', label: 'Default' },
  { value: 'quick-web', label: 'Quick Web Scan' },
  { value: 'owasp-top10', label: 'OWASP Top 10' },
  { value: 'cve-scan', label: 'CVE Detection' },
  { value: 'network-full', label: 'Full Network Scan' },
  { value: 'api-security', label: 'API Security' },
  { value: 'ssl-tls', label: 'SSL/TLS Check' },
  { value: 'pentest-full', label: 'Full Pentest' },
];

export function NewScanModal({ open, onClose, onSubmit, loading }: NewScanModalProps) {
  const [target, setTarget] = useState('');
  const [scanType, setScanType] = useState('webapp');
  const [profile, setProfile] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ target, scan_type: scanType, profile: profile || undefined });
  };

  return (
    <Modal open={open} onClose={onClose} title="New Security Scan">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Target
          </label>
          <Input
            placeholder="https://example.com or 192.168.1.0/24"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            required
          />
          <p className="mt-1 text-xs text-gray-500">
            Enter a URL, IP address, or CIDR range
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Scan Type
          </label>
          <div className="grid grid-cols-2 gap-3">
            {scanTypes.map((type) => (
              <button
                key={type.value}
                type="button"
                onClick={() => setScanType(type.value)}
                className={`flex items-center p-3 rounded-lg border-2 transition-colors ${
                  scanType === type.value
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                    : 'border-gray-200 dark:border-gray-600 hover:border-gray-300'
                }`}
              >
                <type.icon
                  className={`w-5 h-5 mr-2 ${
                    scanType === type.value
                      ? 'text-primary-600'
                      : 'text-gray-400'
                  }`}
                />
                <span
                  className={`text-sm font-medium ${
                    scanType === type.value
                      ? 'text-primary-600'
                      : 'text-gray-700 dark:text-gray-300'
                  }`}
                >
                  {type.label}
                </span>
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Profile (Optional)
          </label>
          <Select
            options={profiles}
            value={profile}
            onChange={(e) => setProfile(e.target.value)}
            placeholder="Select a scan profile"
          />
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={!target || loading}>
            {loading ? 'Starting...' : 'Start Scan'}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
