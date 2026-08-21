"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/use-auth";

export default function CustomerDashboardPage() {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Panel cliente</h1>
        <p className="text-sm text-muted-foreground">
          Bienvenido, {user?.full_name ?? user?.email}
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Servicios disponibles</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Los servicios de reparación, instalación y seguimiento de órdenes
            estarán disponibles en fases posteriores.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}