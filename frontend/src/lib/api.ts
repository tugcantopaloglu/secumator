export interface Finding {
  id: number;
  title: string;
  severity: string;
  description?: string;
  evidence?: string;
  recommendation?: string;
  cve_id?: string;
  affected_component?: string;
}

export interface Scan {
  id: number;
  target: string;
  status: string;
  scan_type: string;
  profile?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  findings_count: number;
  findings?: Finding[];
}

interface DashboardStats {
  overview: { total_scans: number; scans_this_week: number; scans_this_month: number; total_findings: number };
  severity_distribution: Record<string, number>;
  recent_scans: Scan[];
}

interface Trends {
  period_days: number;
  scans_by_day: { date: string; count: number }[];
  findings_by_day: { date: string; count: number }[];
  severity_trend: { severity: string; count: number }[];
}

interface TopVulnerabilities {
  top_vulnerabilities: { title: string; count: number }[];
  most_affected_components: { component: string; count: number }[];
}

const apiBase = `${(process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '')}/api/v1`;

async function responseFor(path: string, options?: RequestInit): Promise<Response> {
  const response = await fetch(`${apiBase}${path}`, options);
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(typeof error?.detail === 'string' ? error.detail : `Request failed (${response.status})`);
  }
  return response;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  return (await responseFor(path, options)).json();
}

function post<T>(path: string, data: unknown): Promise<T> {
  return request<T>(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
}

export const api = {
  getStats: () => request<DashboardStats>('/stats/dashboard'),
  getTrends: (days = 30) => request<Trends>(`/stats/trends?days=${days}`),
  getTopVulnerabilities: () => request<TopVulnerabilities>('/stats/top-vulnerabilities'),
  getScans: (page = 1, limit = 20) => request<{ items: Scan[]; total: number }>(`/scans?limit=${limit}&offset=${Math.max(0, page - 1) * limit}`),
  getScan: (id: string) => request<Scan>(`/scans/${encodeURIComponent(id)}`),
  createScan: (data: { target: string; scan_type: string; profile?: string }) => post<Scan>('/scans', data),
  scanGitHubRepo: (data: { repo_url: string; branch: string; scan_type: string }) => post<Scan>('/github/scan', data),
  getQueueStatus: async () => {
    const status = await request<{ queued: number; running: number; is_processing: boolean }>('/queue/status');
    return { ...status, pending: status.queued };
  },
  getAISummary: (id: string) => request<{ findings_count: number; risk_score: number; risk_level: string; executive_summary: string; top_priorities: string[] }>(`/ai/scan/${encodeURIComponent(id)}/summary`),
  explainVulnerability: (finding: Omit<Finding, 'id'>) => post<Record<string, unknown>>('/ai/explain', finding),
  exportReport: async (id: string, format: string): Promise<Blob> => {
    if (format === 'sarif') {
      return (await responseFor(`/reports/${encodeURIComponent(id)}/sarif`)).blob();
    }
    const report = await post<{ download_url: string }>('/reports', { scan_id: Number(id), format });
    const response = await fetch(`${(process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '')}${report.download_url}`);
    if (!response.ok) throw new Error(`Report download failed (${response.status})`);
    return response.blob();
  },
};
