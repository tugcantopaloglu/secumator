import { api } from '@/lib/api';

const mockFetch = jest.fn();

beforeEach(() => {
  global.fetch = mockFetch;
  mockFetch.mockReset();
});

test('scan creation uses the backend request contract', async () => {
  mockFetch.mockResolvedValue({ ok: true, json: async () => ({ id: 7 }) });
  await api.createScan({ target: 'https://example.test', scan_type: 'webapp' });
  expect(mockFetch).toHaveBeenCalledWith('/api/v1/scans', expect.objectContaining({
    method: 'POST', body: JSON.stringify({ target: 'https://example.test', scan_type: 'webapp' }),
  }));
});

test('scan pagination maps a page to the API offset', async () => {
  mockFetch.mockResolvedValue({ ok: true, json: async () => ({ items: [], total: 0 }) });
  await api.getScans(3, 20);
  expect(mockFetch).toHaveBeenCalledWith('/api/v1/scans?limit=20&offset=40', undefined);
});

test('backend failures remain visible to callers', async () => {
  mockFetch.mockResolvedValue({ ok: false, status: 400, json: async () => ({ detail: 'Invalid target' }) });
  await expect(api.getStats()).rejects.toThrow('Invalid target');
});

test('report creation is followed by the returned download endpoint', async () => {
  const blob = new Blob(['report']);
  mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ download_url: '/api/v1/reports/download/fixture.html' }) });
  mockFetch.mockResolvedValueOnce({ ok: true, blob: async () => blob });
  expect(await api.exportReport('7', 'html')).toBe(blob);
  expect(mockFetch).toHaveBeenLastCalledWith('/api/v1/reports/download/fixture.html');
});
