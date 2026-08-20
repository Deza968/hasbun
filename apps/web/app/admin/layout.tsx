"use client";

import { RequireAuth } from "@/components/guards";
import { Sidebar } from "@/components/sidebar";

const items = [
  { href: "/admin", label: "Panel" },
  { href: "/admin/users", label: "Usuarios" },
  { href: "/profile", label: "Mi perfil" },
];

export default function AdminLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <RequireAuth>
      <div className="flex min-h-screen">
        <Sidebar title="Panel admin" items={items} />
        <main className="flex-1 p-6">{children}</main>
      </div>
    </RequireAuth>
  );
}