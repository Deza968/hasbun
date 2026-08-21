"use client";

import { RequireAuth } from "@/components/guards";
import { Sidebar } from "@/components/sidebar";
import { useAuth } from "@/hooks/use-auth";
import { canAccessSection } from "@/lib/permissions";

const allItems = [
  { href: "/admin", label: "Panel", section: "panel" },
  { href: "/admin/productos", label: "Productos", section: "productos" },
  { href: "/admin/categorias", label: "Categorías", section: "categorias" },
  { href: "/admin/marcas", label: "Marcas", section: "marcas" },
  { href: "/admin/atributos", label: "Atributos", section: "atributos" },
  { href: "/admin/inventario", label: "Inventario", section: "inventario" },
  { href: "/admin/proveedores", label: "Proveedores", section: "proveedores" },
  { href: "/admin/compras", label: "Compras", section: "compras" },
  { href: "/admin/users", label: "Usuarios", section: "users" },
  { href: "/profile", label: "Mi perfil", section: "profile" },
];

export default function AdminLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const { user } = useAuth();
  const items = allItems.filter((i) => canAccessSection(user, i.section));

  return (
    <RequireAuth>
      <div className="flex min-h-screen">
        <Sidebar title="Panel admin" items={items} />
        <main className="flex-1 p-6">{children}</main>
      </div>
    </RequireAuth>
  );
}