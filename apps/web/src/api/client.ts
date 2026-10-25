const API_BASE = '/api/v1';

export class ApiClient {
  private static token: string | null = localStorage.getItem('trustcounsel_token');

  static setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('trustcounsel_token', token);
    } else {
      localStorage.removeItem('trustcounsel_token');
    }
  }

  static getToken(): string | null {
    return this.token;
  }

  private static getHeaders(isJson = true): HeadersInit {
    const headers: Record<string, string> = {};
    if (isJson) {
      headers['Content-Type'] = 'application/json';
    }
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  }

  static async get<T>(endpoint: string): Promise<T> {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      headers: this.getHeaders(true),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ message: res.statusText }));
      throw new Error(err.message || `Request failed with status ${res.status}`);
    }
    return res.json();
  }

  static async post<T>(endpoint: string, body?: any, isJson = true): Promise<T> {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: isJson ? this.getHeaders(true) : (this.token ? { Authorization: `Bearer ${this.token}` } : {}),
      body: isJson ? (body ? JSON.stringify(body) : undefined) : body,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ message: res.statusText }));
      throw new Error(err.message || `Request failed with status ${res.status}`);
    }
    return res.json();
  }

  static async delete<T>(endpoint: string): Promise<T> {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: 'DELETE',
      headers: this.getHeaders(true),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ message: res.statusText }));
      throw new Error(err.message || `Request failed with status ${res.status}`);
    }
    return res.json();
  }
}
