"use client";

import { RequireAuth } from "@/components/guards";
import { Sidebar } from "@/components/sidebar";

const items = [
  { href: "/customer", label: "Panel" },
  { href: "/profile", label: "Mi perfil" },
];

export default function CustomerLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <RequireAuth>
      <div className="flex min-h-screen">
        <Sidebar title="Panel cliente" items={items} />
        <main className="flex-1 p-6">{children}</main>
      </div>
    </RequireAuth>
  );
}