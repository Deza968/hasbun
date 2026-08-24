import type { User } from "./types";

const SECTION_PERMISSIONS: Record<string, string[]> = {
  productos: ["productos.ver"],
  categorias: ["categorias.gestionar"],
  marcas: ["marcas.gestionar"],
  atributos: ["productos.editar"],
  users: ["usuarios.ver"],
  panel: ["reportes.propios"],
  inventario: ["inventario.ver"],
  proveedores: ["proveedores.gestionar"],
  compras: ["compras.ver"],
  creditos: ["creditos.ver"],
  cuotas: ["cuotas.gestionar"],
  morosidad: ["creditos.aprobar"],
};

export function userPermissions(user: User | null): string[] {
  if (!user) return [];
  if (user.is_superuser) return ["*"];
  return user.permissions ?? [];
}

export function hasPermission(user: User | null, codename: string): boolean {
  const perms = userPermissions(user);
  return perms.includes("*") || perms.includes(codename);
}

export function canAccessSection(user: User | null, section: string): boolean {
  if (user?.is_superuser) return true;
  const required = SECTION_PERMISSIONS[section];
  if (!required) return true;
  return required.some((p) => hasPermission(user, p));
}