"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { fetchDelinquency } from "@/lib/credits-api";
import { getErrorMessage, isForbidden } from "@/lib/api";
import { RequireSection } from "@/components/guards";

export default function MorosidadPage() {
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);

  const delinquencyQuery = useQuery({
    queryKey: ["delinquency"],
    queryFn: fetchDelinquency,
  });

  useEffect(() => {
    if (isForbidden(delinquencyQuery.error)) setForbidden(true);
    else if (delinquencyQuery.error)
      setError(getErrorMessage(delinquencyQuery.error));
  }, [delinquencyQuery.error]);

  if (forbidden) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-destructive">
          Solo el propietario puede ver la morosidad.
        </CardContent>
      </Card>
    );
  }

  const data = delinquencyQuery.data;

  return (
    <RequireSection section="morosidad">
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Morosidad</h1>
          <p className="text-sm text-muted-foreground">
            Clientes con cuotas vencidas y mora acumulada
          </p>
        </div>

        {error && (
          <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}

        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Mora total en el sistema
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-semibold text-destructive">
                S/ {data?.mora_system_total ?? "—"}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Clientes afectados
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-semibold">{data?.affected_customers ?? "—"}</p>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardContent className="p-0">
            {delinquencyQuery.isLoading ? (
              <div className="flex justify-center py-10">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Cliente</TableHead>
                    <TableHead className="text-right">Créditos activos</TableHead>
                    <TableHead className="text-right">Cuotas vencidas</TableHead>
                    <TableHead className="text-right">Capital vencido</TableHead>
                    <TableHead className="text-right">Mora</TableHead>
                    <TableHead className="text-right">Mayor atraso</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(data?.rows ?? []).map((r) => (
                    <TableRow key={r.customer_id}>
                      <TableCell className="font-medium">
                        {r.customer_name ?? "—"}
                      </TableCell>
                      <TableCell className="text-right">{r.active_credits}</TableCell>
                      <TableCell className="text-right text-destructive">
                        {r.overdue_installments}
                      </TableCell>
                      <TableCell className="text-right">
                        S/ {r.overdue_capital}
                      </TableCell>
                      <TableCell className="text-right font-medium text-destructive">
                        S/ {r.mora_total}
                      </TableCell>
                      <TableCell className="text-right">
                        {r.days_late_max} días
                      </TableCell>
                      <TableCell className="space-x-1 text-right">
                        <Button variant="ghost" size="sm" asChild>
                          <Link href={`/admin/clientes/${r.customer_id}`}>Cliente</Link>
                        </Button>
                        <Button variant="ghost" size="sm" asChild>
                          <Link href="/admin/cuotas">Cuotas</Link>
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {(data?.rows?.length ?? 0) === 0 && (
                    <TableRow>
                      <TableCell
                        colSpan={7}
                        className="py-8 text-center text-sm text-muted-foreground"
                      >
                        Sin clientes morosos
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </RequireSection>
  );
}
