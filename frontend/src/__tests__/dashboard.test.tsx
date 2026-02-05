import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import DashboardPage from '@/app/page';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

jest.mock('@/lib/api', () => ({
  api: {
    getStats: jest.fn().mockResolvedValue({
      overview: {
        total_scans: 100,
        scans_this_week: 10,
        scans_this_month: 40,
        total_findings: 500,
      },
      severity_distribution: {
        critical: 5,
        high: 20,
        medium: 100,
        low: 200,
        info: 175,
      },
      recent_scans: [],
    }),
    getTrends: jest.fn().mockResolvedValue({
      period_days: 30,
      scans_by_day: [],
      findings_by_day: [],
      severity_trend: [],
    }),
    getTopVulnerabilities: jest.fn().mockResolvedValue({
      top_vulnerabilities: [],
      most_affected_components: [],
    }),
  },
}));

describe('Dashboard Page', () => {
  it('renders the dashboard title', () => {
    render(<DashboardPage />, { wrapper });
    expect(screen.getByText('Security Dashboard')).toBeInTheDocument();
  });

  it('renders stats cards', () => {
    render(<DashboardPage />, { wrapper });
    expect(screen.getByText('Total Scans')).toBeInTheDocument();
    expect(screen.getByText('This Week')).toBeInTheDocument();
    expect(screen.getByText('This Month')).toBeInTheDocument();
    expect(screen.getByText('Total Findings')).toBeInTheDocument();
  });
});
