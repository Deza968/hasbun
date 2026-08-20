"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/hooks/use-auth";

export default function AdminDashboardPage() {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Panel admin</h1>
        <p className="text-sm text-muted-foreground">
          Bienvenido, {user?.full_name ?? user?.email}
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Permisos asignados</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {(user?.permissions ?? []).length === 0 && (
              <p className="text-sm text-muted-foreground">
                Sin permisos directos.
              </p>
            )}
            {(user?.permissions ?? []).map((p) => (
              <Badge key={p} variant="secondary">
                {p}
              </Badge>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Roles</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {(user?.roles ?? []).map((r) => (
              <Badge key={r}>{r}</Badge>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}