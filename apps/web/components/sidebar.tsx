"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LogOut, User } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/use-auth";

export interface NavItem {
  href: string;
  label: string;
}

export function Sidebar({
  title,
  items,
}: {
  title: string;
  items: NavItem[];
}) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="flex w-64 shrink-0 flex-col border-r bg-muted/40">
      <div className="border-b px-4 py-4">
        <p className="font-semibold">{title}</p>
        <p className="text-xs text-muted-foreground">
          {user?.full_name ?? user?.email}
        </p>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {items.map((item) => {
          const active =
            pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center rounded-md px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-accent hover:text-accent-foreground"
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="flex items-center gap-2 border-t p-3">
        {user?.roles.map((role) => (
          <Badge key={role} variant="secondary" className="capitalize">
            {role}
          </Badge>
        ))}
        <div className="ml-auto flex gap-1">
          <Button variant="ghost" size="icon" asChild title="Perfil">
            <Link href="/profile">
              <User className="h-4 w-4" />
            </Link>
          </Button>
          <Button
            variant="ghost"
            size="icon"
            title="Cerrar sesión"
            onClick={() => void logout()}
          >
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </aside>
  );
}