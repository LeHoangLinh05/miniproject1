/**
 * Axios instance với Request + Response Interceptors.
 *
 * Luồng hoạt động (khớp với auth-flow.md):
 *   Request interceptor  → tự động gắn Authorization: Bearer <AT>
 *   Response interceptor → nếu nhận 401:
 *     1. Gọi POST /api/token/refresh (browser tự gửi cookie refresh_token)
 *     2. Lưu access_token mới vào memory
 *     3. Retry request cũ với token mới
 *     4. Nếu refresh thất bại → dispatch custom event "auth-logout"
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

// ---------------------------------------------------------------------------
// 1. In-memory access token
// ---------------------------------------------------------------------------
let memoryAccessToken: string | null = null;

export const setMemoryToken = (token: string | null): void => {
  memoryAccessToken = token;
};

export const getMemoryToken = (): string | null => memoryAccessToken;

// ---------------------------------------------------------------------------
// 2. Axios instance
// ---------------------------------------------------------------------------
export const api = axios.create({
  // Next.js rewrite: /api/* → backend (xem next.config.ts)
  baseURL: "/api",
  withCredentials: true, // gửi HttpOnly cookie refresh_token tự động
  headers: {
    "Content-Type": "application/json",
  },
});

// ---------------------------------------------------------------------------
// 3. Request interceptor — gắn Bearer token
// ---------------------------------------------------------------------------
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (memoryAccessToken) {
      config.headers.Authorization = `Bearer ${memoryAccessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ---------------------------------------------------------------------------
// 4. Response interceptor — 401 → refresh → retry
// ---------------------------------------------------------------------------

// Tránh gọi refresh nhiều lần khi nhiều request cùng nhận 401
let isRefreshing = false;
type QueueItem = { resolve: (token: string) => void; reject: (err: unknown) => void };
let queue: QueueItem[] = [];

const processQueue = (error: unknown, token: string | null) => {
  queue.forEach(({ resolve, reject }) => {
    if (error) reject(error);
    else resolve(token as string);
  });
  queue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    const is401 = error.response?.status === 401;
    const isRefreshEndpoint = originalRequest?.url?.includes("/token/refresh");
    const alreadyRetried = originalRequest?._retry;

    if (!is401 || isRefreshEndpoint || alreadyRetried) {
      return Promise.reject(error);
    }

    if (isRefreshing) {
      // Xếp hàng chờ refresh đang chạy
      return new Promise<string>((resolve, reject) => {
        queue.push({ resolve, reject });
      }).then((newToken) => {
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      });
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      // Refresh — browser tự gửi cookie refresh_token (withCredentials: true)
      const { data } = await api.post<{ access_token: string }>("/token/refresh");
      const newToken = data.access_token;

      setMemoryToken(newToken);

      /*
       * REDUX PLACEHOLDER:
       * import { store } from '@/redux/store';
       * import { setAccessToken } from '@/redux/slices/authSlice';
       * store.dispatch(setAccessToken(newToken));
       */

      processQueue(null, newToken);

      originalRequest.headers.Authorization = `Bearer ${newToken}`;
      return api(originalRequest);
    } catch (refreshError) {
      processQueue(refreshError, null);
      setMemoryToken(null);

      /*
       * REDUX PLACEHOLDER:
       * store.dispatch(clearAccessToken());
       */

      // Thông báo cho AuthContext đăng xuất
      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("auth-logout"));
      }

      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);
