const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

async function fetcher(endpoint: string, options: RequestInit = {}) {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    if (response.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    const error = await response.json().catch(() => ({ message: 'An error occurred' }));
    throw new Error(error.message || response.statusText);
  }

  if (response.status === 204) return null;
  return response.json();
}

export const api = {
  auth: {
    login: (credentials: any) => fetcher('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    }),
    register: (data: any) => fetcher('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    me: () => fetcher('/auth/me'),
  },
  stores: {
    list: () => fetcher('/stores'),
    get: (id: string) => fetcher(`/stores/${id}`),
    create: (data: any) => fetcher('/stores', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  },
  cameras: {
    list: (storeId: string) => fetcher(`/stores/${storeId}/cameras`),
    get: (id: string) => fetcher(`/cameras/${id}`),
    update: (id: string, data: any) => fetcher(`/cameras/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  },
  events: {
    list: (params?: any) => {
      const query = params ? `?${new URLSearchParams(params).toString()}` : '';
      return fetcher(`/events${query}`);
    },
    get: (id: string) => fetcher(`/events/${id}`),
  },
  dashboard: {
    stats: () => fetcher('/dashboard/stats'),
    recent: () => fetcher('/dashboard/recent'),
  },
};
