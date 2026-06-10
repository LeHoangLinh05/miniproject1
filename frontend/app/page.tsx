"use client";
import React, { useEffect, useState } from "react";
import { useAuth } from "@/components/auth-context";
import { api } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { AxiosError } from "axios";

interface UserStatus {
  user_id: number;
  email: string;
  role: string;
  is_online: boolean;
  last_active_at?: string | null;
  offline_minutes?: number | null;
}

export default function Home() {
  const { user, logout, isLoading } = useAuth();
  const [usersList, setUsersList] = useState<UserStatus[]>([]);
  const [adminError, setAdminError] = useState("");
  const [fetchingUsers, setFetchingUsers] = useState(false);

  const fetchAllUsers = async () => {
    if (user?.role !== "admin") return;
    setFetchingUsers(true);
    setAdminError("");
    try {
      const { data } = await api.get<UserStatus[]>("/users/all");
      setUsersList(data);
    } catch (err) {
      const axiosErr = err as AxiosError<{ detail: string }>;
      setAdminError(
        axiosErr.response?.data?.detail || "Không thể tải danh sách người dùng"
      );
    } finally {
      setFetchingUsers(false);
    }
  };

  useEffect(() => {
    if (user?.role === "admin") {
      fetchAllUsers();
    }
  }, [user]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-zinc-950">
        <p className="text-zinc-500">Đang tải trạng thái xác thực...</p>
      </div>
    );
  }

  if (!user) {
    return null; // AuthContext handles redirect to /login
  }

  return (
    <div className="flex flex-col min-h-screen bg-zinc-50 dark:bg-zinc-950 p-6 md:p-12">
      <main className="max-w-4xl mx-auto w-full space-y-8">
        
        {/* Header Section */}
        <div className="flex items-center justify-between border-b pb-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Hệ Thống Xác Thực</h1>
            <p className="text-muted-foreground mt-1">Đăng nhập thành công bằng JWT Auth Flow</p>
          </div>
          <Button variant="destructive" onClick={logout}>
            Đăng xuất
          </Button>
        </div>

        {/* Current User Info Card */}
        <div className="bg-white dark:bg-zinc-900 border rounded-lg p-6 space-y-4 shadow-sm">
          <h2 className="text-xl font-semibold">Thông tin tài khoản của bạn</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="p-3 bg-zinc-50 dark:bg-zinc-800 rounded border">
              <span className="text-zinc-500 block mb-1">Email</span>
              <span className="font-mono font-medium">{user.email}</span>
            </div>
            <div className="p-3 bg-zinc-50 dark:bg-zinc-800 rounded border">
              <span className="text-zinc-500 block mb-1">Vai trò (Role)</span>
              <span className="font-medium capitalize">{user.role}</span>
            </div>
            <div className="p-3 bg-zinc-50 dark:bg-zinc-800 rounded border">
              <span className="text-zinc-500 block mb-1">Trạng thái</span>
              <span className="inline-flex items-center gap-1.5 font-medium text-green-600 dark:text-green-400">
                <span className="h-2 w-2 rounded-full bg-green-600 dark:bg-green-400 animate-pulse" />
                Online
              </span>
            </div>
          </div>
        </div>

        {/* Admin Section */}
        {user.role === "admin" && (
          <div className="bg-white dark:bg-zinc-900 border rounded-lg p-6 space-y-4 shadow-sm">
            <div className="flex items-center justify-between border-b pb-3">
              <h2 className="text-xl font-semibold text-red-600 dark:text-red-400">
                Khu vực Quản trị (Admin Only)
              </h2>
              <Button size="sm" onClick={fetchAllUsers} disabled={fetchingUsers}>
                {fetchingUsers ? "Đang tải..." : "Tải lại danh sách"}
              </Button>
            </div>

            {adminError && (
              <div className="p-3 text-sm text-red-600 bg-red-50 dark:bg-red-950/30 dark:text-red-400 rounded-lg">
                {adminError}
              </div>
            )}

            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left border-collapse">
                <thead>
                  <tr className="border-b bg-zinc-50 dark:bg-zinc-800/50">
                    <th className="p-3 font-semibold text-zinc-600 dark:text-zinc-400">User ID</th>
                    <th className="p-3 font-semibold text-zinc-600 dark:text-zinc-400">Email</th>
                    <th className="p-3 font-semibold text-zinc-600 dark:text-zinc-400">Role</th>
                    <th className="p-3 font-semibold text-zinc-600 dark:text-zinc-400">Trạng thái</th>
                    <th className="p-3 font-semibold text-zinc-600 dark:text-zinc-400">Hoạt động lần cuối</th>
                    <th className="p-3 font-semibold text-zinc-600 dark:text-zinc-400">Số phút offline</th>
                  </tr>
                </thead>
                <tbody>
                  {usersList.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="p-4 text-center text-zinc-500">
                        {fetchingUsers ? "Đang tải dữ liệu..." : "Chưa có dữ liệu người dùng."}
                      </td>
                    </tr>
                  ) : (
                    usersList.map((u) => (
                      <tr key={u.user_id} className="border-b hover:bg-zinc-50/50 dark:hover:bg-zinc-800/30">
                        <td className="p-3 font-mono">{u.user_id}</td>
                        <td className="p-3 font-medium">{u.email}</td>
                        <td className="p-3 capitalize">{u.role}</td>
                        <td className="p-3">
                          {u.is_online ? (
                            <span className="inline-flex items-center gap-1 text-green-600 dark:text-green-400">
                              <span className="h-1.5 w-1.5 rounded-full bg-green-600 dark:bg-green-400" />
                              Online
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-zinc-400">
                              <span className="h-1.5 w-1.5 rounded-full bg-zinc-400" />
                              Offline
                            </span>
                          )}
                        </td>
                        <td className="p-3 text-zinc-500">
                          {u.last_active_at ? new Date(u.last_active_at).toLocaleString("vi-VN") : "-"}
                        </td>
                        <td className="p-3 font-mono">
                          {u.is_online ? "0" : u.offline_minutes !== null ? u.offline_minutes : "-"}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

      </main>
    </div>
  );
}
