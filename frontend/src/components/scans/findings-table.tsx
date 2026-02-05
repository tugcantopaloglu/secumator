'use client';

import { useState } from 'react';
import { clsx } from 'clsx';
import { ChevronDown, ChevronRight, ExternalLink, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Modal } from '@/components/ui/modal';
import { api } from '@/lib/api';

interface Finding {
  id: number;
  title: string;
  severity: string;
  description?: string;
  evidence?: string;
  recommendation?: string;
  cve_id?: string;
  cvss_score?: number;
  affected_component?: string;
  source_tool?: string;
}

interface FindingsTableProps {
  findings?: Finding[];
  loading?: boolean;
}

const severityColors: Record<string, string> = {
  critical: 'severity-critical',
  high: 'severity-high',
  medium: 'severity-medium',
  low: 'severity-low',
  info: 'severity-info',
};

export function FindingsTable({ findings, loading }: FindingsTableProps) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const [aiModal, setAiModal] = useState<{ open: boolean; finding?: Finding; data?: any; loading: boolean }>({
    open: false,
    loading: false,
  });

  const toggleExpand = (id: number) => {
    const newExpanded = new Set(expanded);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpanded(newExpanded);
  };

  const getAIExplanation = async (finding: Finding) => {
    setAiModal({ open: true, finding, loading: true });
    try {
      const data = await api.explainVulnerability({
        title: finding.title,
        severity: finding.severity,
        description: finding.description,
        cve_id: finding.cve_id,
        affected_component: finding.affected_component,
      });
      setAiModal((prev) => ({ ...prev, data, loading: false }));
    } catch (error) {
      setAiModal((prev) => ({ ...prev, loading: false }));
    }
  };

  if (loading) {
    return (
      <div className="animate-pulse p-6">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="py-4 border-b border-gray-200 dark:border-gray-700">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2" />
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
          </div>
        ))}
      </div>
    );
  }

  if (!findings?.length) {
    return (
      <div className="p-12 text-center text-gray-500">No findings to display</div>
    );
  }

  return (
    <>
      <div className="divide-y divide-gray-200 dark:divide-gray-700">
        {findings.map((finding) => (
          <div key={finding.id}>
            <div
              className="px-6 py-4 flex items-center cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
              onClick={() => toggleExpand(finding.id)}
            >
              <div className="mr-3">
                {expanded.has(finding.id) ? (
                  <ChevronDown className="w-5 h-5 text-gray-400" />
                ) : (
                  <ChevronRight className="w-5 h-5 text-gray-400" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3">
                  <span className={clsx('severity-badge', severityColors[finding.severity])}>
                    {finding.severity}
                  </span>
                  <h4 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {finding.title}
                  </h4>
                </div>
                <div className="flex items-center gap-3 mt-1">
                  {finding.cve_id && (
                    <span className="text-xs text-blue-600 dark:text-blue-400">
                      {finding.cve_id}
                    </span>
                  )}
                  {finding.cvss_score && (
                    <span className="text-xs text-gray-500">
                      CVSS: {finding.cvss_score}
                    </span>
                  )}
                  {finding.source_tool && (
                    <span className="text-xs text-gray-400">{finding.source_tool}</span>
                  )}
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  getAIExplanation(finding);
                }}
              >
                <Sparkles className="w-4 h-4 mr-1 text-purple-500" />
                AI
              </Button>
            </div>

            {expanded.has(finding.id) && (
              <div className="px-6 py-4 bg-gray-50 dark:bg-gray-900/50 border-t border-gray-200 dark:border-gray-700">
                <div className="ml-8 space-y-4">
                  {finding.affected_component && (
                    <div>
                      <h5 className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        Affected Component
                      </h5>
                      <code className="text-sm text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded mt-1 inline-block">
                        {finding.affected_component}
                      </code>
                    </div>
                  )}
                  {finding.description && (
                    <div>
                      <h5 className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        Description
                      </h5>
                      <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">
                        {finding.description}
                      </p>
                    </div>
                  )}
                  {finding.evidence && (
                    <div>
                      <h5 className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        Evidence
                      </h5>
                      <pre className="text-xs text-gray-700 dark:text-gray-300 mt-1 bg-gray-100 dark:bg-gray-800 p-3 rounded overflow-x-auto">
                        {finding.evidence}
                      </pre>
                    </div>
                  )}
                  {finding.recommendation && (
                    <div>
                      <h5 className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        Recommendation
                      </h5>
                      <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">
                        {finding.recommendation}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <Modal
        open={aiModal.open}
        onClose={() => setAiModal({ open: false, loading: false })}
        title="AI Vulnerability Analysis"
        className="max-w-2xl"
      >
        {aiModal.loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
          </div>
        ) : aiModal.data ? (
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-gray-100 dark:bg-gray-700 rounded-lg">
                <p className="text-xs text-gray-500">Risk Score</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {aiModal.data.risk_score}/10
                </p>
              </div>
              <div className="p-3 bg-gray-100 dark:bg-gray-700 rounded-lg">
                <p className="text-xs text-gray-500">Exploitation</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">
                  {aiModal.data.exploitation_likelihood}
                </p>
              </div>
            </div>

            <div>
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Explanation
              </h4>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {aiModal.data.explanation}
              </p>
            </div>

            <div>
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Business Impact
              </h4>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {aiModal.data.business_impact}
              </p>
            </div>

            <div>
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Risk Factors
              </h4>
              <ul className="list-disc list-inside text-sm text-gray-600 dark:text-gray-400">
                {aiModal.data.risk_factors?.map((factor: string, i: number) => (
                  <li key={i}>{factor}</li>
                ))}
              </ul>
            </div>
          </div>
        ) : null}
      </Modal>
    </>
  );
}
