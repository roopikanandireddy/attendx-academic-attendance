import axios from 'axios';

const rawApiUrl = import.meta.env.VITE_API_URL;
const API_URL = (rawApiUrl && typeof rawApiUrl === 'string' && rawApiUrl.trim())
  ? rawApiUrl.trim().replace(/\/+$/, '')
  : 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor — attach token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('attendx_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor — handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('attendx_token');
      localStorage.removeItem('attendx_user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
