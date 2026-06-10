"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { api, setMemoryToken } from "@/lib/auth";
import { AxiosError } from "axios";

interface User {
  user_id: number;
  email: string;
  role: string;
  is_online: boolean;
  last_active_at?: string | null;
  offline_minutes?: number | null;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (email: string, password: string, role?: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  const fetchProfile = async (): Promise<void> => {
    try {
      const { data } = await api.get<User>("/users/me");
      setUser(data);
    } catch {
      setUser(null);
      setMemoryToken(null);
    } finally {
      setIsLoading(false);
    }
  };

  // Khởi tạo: thử refresh để kiểm tra session còn hợp lệ không
  useEffect(() => {
    const initAuth = async () => {
      try {
        // Browser tự gửi cookie refresh_token (withCredentials: true)
        const { data } = await api.post<{ access_token: string }>("/token/refresh");
        setMemoryToken(data.access_token);

        /*
         * REDUX PLACEHOLDER:
         * import { store } from '@/redux/store';
         * import { setAccessToken } from '@/redux/slices/authSlice';
         * store.dispatch(setAccessToken(data.access_token));
         */

        await fetchProfile();
      } catch {
        // Không có session hợp lệ → user chưa đăng nhập
        setIsLoading(false);
      }
    };

    initAuth();

    // Lắng nghe sự kiện đăng xuất từ response interceptor khi refresh thất bại
    const handleLogoutEvent = () => {
      setUser(null);
      setMemoryToken(null);
      router.push("/login");
    };

    window.addEventListener("auth-logout", handleLogoutEvent);
    return () => {
      window.removeEventListener("auth-logout", handleLogoutEvent);
    };
  }, [router]);

  // Route protection
  useEffect(() => {
    if (isLoading) return;

    const publicPages = ["/login", "/register"];
    const isPublicPage = publicPages.includes(pathname);

    if (!user && !isPublicPage) {
      router.push("/login");
    } else if (user && isPublicPage) {
      router.push("/");
    }
  }, [user, isLoading, pathname, router]);

  const login = async (
    email: string,
    password: string
  ): Promise<{ success: boolean; error?: string }> => {
    try {
      const { data } = await api.post<{ access_token: string }>("/login", {
        email,
        password,
      });

      setMemoryToken(data.access_token);

      /*
       * REDUX PLACEHOLDER:
       * store.dispatch(setAccessToken(data.access_token));
       */

      await fetchProfile();
      router.push("/");
      return { success: true };
    } catch (err) {
      const axiosErr = err as AxiosError<{ detail: string }>;
      const message =
        axiosErr.response?.data?.detail || "Đăng nhập thất bại";
      return { success: false, error: message };
    }
  };

  const register = async (
    email: string,
    password: string,
    role: string = "user"
  ): Promise<{ success: boolean; error?: string }> => {
    try {
      await api.post("/register", { email, password, role });
      return { success: true };
    } catch (err) {
      const axiosErr = err as AxiosError<{ detail: string }>;
      const message =
        axiosErr.response?.data?.detail || "Đăng ký thất bại";
      return { success: false, error: message };
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await api.post("/logout");
    } catch {
      // Bỏ qua lỗi logout — vẫn xóa state phía client
    } finally {
      setUser(null);
      setMemoryToken(null);

      /*
       * REDUX PLACEHOLDER:
       * store.dispatch(clearAccessToken());
       */

      router.push("/login");
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        refreshProfile: fetchProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
