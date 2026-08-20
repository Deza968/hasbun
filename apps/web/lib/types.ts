export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
  phone: string | null;
  is_active: boolean;
  is_superuser: boolean;
  last_login_at: string | null;
  created_at: string;
  roles: string[];
  permissions?: string[];
}

export interface UserList {
  items: User[];
  total: number;
}

export interface Role {
  id: string;
  code: string;
  name: string;
  description: string | null;
  is_system: boolean;
  created_at: string;
  permissions: string[];
}

export interface Permission {
  id: string;
  code: string;
  module: string;
  description: string | null;
}

export interface AuditLog {
  id: string;
  action: string;
  module: string;
  user_email: string | null;
  entity_type: string | null;
  entity_id: string | null;
  old_values: Record<string, unknown> | null;
  new_values: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditList {
  items: AuditLog[];
  total: number;
}