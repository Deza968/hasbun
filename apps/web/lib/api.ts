import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "/api/v1";

export const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

interface RetryConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as RetryConfig | undefined;
    const status = error.response?.status;

    if (
      status === 401 &&
      config &&
      !config._retry &&
      !config.url?.includes("/auth/login") &&
      !config.url?.includes("/auth/refresh")
    ) {
      config._retry = true;
      try {
        await api.post("/auth/refresh");
        return await api.request(config);
      } catch {
        window.location.href = "/login";
        return Promise.reject(error);
      }
    }
    return Promise.reject(error);
  }
);

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail =
      error.response?.data as
        | { detail?: string; message?: string; error?: { message?: string } }
        | undefined;
    return (
      detail?.error?.message ??
      detail?.detail ??
      detail?.message ??
      "Error inesperado"
    );
  }
  return "Error inesperado";
}

export function isForbidden(error: unknown): boolean {
  return axios.isAxiosError(error) && error.response?.status === 403;
}