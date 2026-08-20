import { api } from "./api";
import type { AuditList, Permission, Role, User, UserList } from "./types";

export async function login(
  email: string,
  password: string
): Promise<User> {
  const { data } = await api.post<User>("/auth/login", { email, password });
  return data;
}

export async function logout(): Promise<void> {
  await api.post("/auth/logout");
}

export async function getMe(): Promise<User> {
  const { data } = await api.get<User>("/auth/me");
  return data;
}

export async function changePassword(
  currentPassword: string,
  newPassword: string
): Promise<void> {
  await api.post("/auth/change-password", {
    current_password: currentPassword,
    new_password: newPassword,
  });
}

export async function updateOwnProfile(payload: {
  full_name?: string;
  phone?: string | null;
}): Promise<User> {
  const { data } = await api.put<User>("/users/me", payload);
  return data;
}

export async function fetchUsers(): Promise<UserList> {
  const { data } = await api.get<UserList>("/users");
  return data;
}

export async function createUser(payload: {
  email: string;
  username: string;
  full_name: string;
  phone?: string | null;
  password: string;
  role_codes: string[];
}): Promise<User> {
  const { data } = await api.post<User>("/users", payload);
  return data;
}

export async function updateUser(
  userId: string,
  payload: { full_name?: string; phone?: string | null; is_active?: boolean }
): Promise<User> {
  const { data } = await api.patch<User>(`/users/${userId}`, payload);
  return data;
}

export async function deactivateUser(userId: string): Promise<void> {
  await api.delete(`/users/${userId}`);
}

export async function assignRole(
  userId: string,
  roleCode: string
): Promise<User> {
  const { data } = await api.post<User>(
    `/users/${userId}/roles`,
    { role_code: roleCode }
  );
  return data;
}

export async function removeRole(
  userId: string,
  roleCode: string
): Promise<User> {
  const { data } = await api.delete<User>(`/users/${userId}/roles/${roleCode}`);
  return data;
}

export async function setPermissionOverride(
  userId: string,
  codename: string,
  granted: boolean,
  reason?: string
): Promise<User> {
  const { data } = await api.post<User>(
    `/users/${userId}/permissions`,
    { codename, granted, reason }
  );
  return data;
}

export async function fetchRoles(): Promise<Role[]> {
  const { data } = await api.get<Role[]>("/roles");
  return data;
}

export async function fetchPermissions(): Promise<Permission[]> {
  const { data } = await api.get<Permission[]>("/permissions");
  return data;
}

export async function fetchAudit(page = 1, perPage = 20): Promise<AuditList> {
  const { data } = await api.get<AuditList>("/audit", {
    params: { page, per_page: perPage },
  });
  return data;
}