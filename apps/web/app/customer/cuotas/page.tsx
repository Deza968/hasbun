"use client";

import { useQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { AGREEMENT_STATUS_BADGE, AGREEMENT_STATUS_LABELS, fetchMyCredits } from "@/lib/credits-api";
import { getErrorMessage } from "@/lib/api";

function installmentGlyph(status: string, hasMora: boolean): string {
  switch (status) {
    case "PAID":
      return "✅";
    case "PARTIALLY_PAID":
      return "◐";
    case "OVERDUE":
      return "⚠️";
    default:
      return "☐";
  }
}

export default function MisCuotasPage() {
  const creditsQuery = useQuery({
    queryKey: ["my-credits"],
    queryFn: fetchMyCredits,
  });

  if (creditsQuery.isLoading) {
    return (
      <div className="flex justify-center py-10">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (creditsQuery.error) {
    return (
      <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
        {getErrorMessage(creditsQuery.error)}
      </p>
    );
  }

  const credits = creditsQuery.data ?? [];

  if (credits.length === 0) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold">Mis cuotas</h1>
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            No tienes créditos registrados.
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Mis cuotas</h1>

      {credits.map((c) => {
        const pending = c.installments
          .filter((i) => i.status !== "PAID")
          .reduce((acc, i) => acc + parseFloat(i.total_due), 0);
        const next = c.installments.find((i) => i.status !== "PAID");
        const history = c.installments.filter((i) => parseFloat(i.paid_amount) > 0);

        return (
          <Card key={c.id}>
            <CardHeader className="flex-row items-center justify-between space-y-0">
              <div>
                <CardTitle>{c.code}</CardTitle>
                <CardDescription>
                  {c.number_of_installments} cuotas · financiado S/{" "}
                  {c.financed_amount}
                </CardDescription>
              </div>
              <Badge variant={AGREEMENT_STATUS_BADGE[c.status] ?? "secondary"}>
                {AGREEMENT_STATUS_LABELS[c.status] ?? c.status}
              </Badge>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm">
                Pendiente total:{" "}
                <span className="text-lg font-semibold">S/ {pending.toFixed(2)}</span>
                {next && (
                  <span className="ml-3 text-muted-foreground">
                    Próxima cuota: #{next.number} · S/ {next.total_due} · vence{" "}
                    {next.due_date}
                  </span>
                )}
              </p>

              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead />
                    <TableHead>#</TableHead>
                    <TableHead>Vencimiento</TableHead>
                    <TableHead className="text-right">Pagado</TableHead>
                    <TableHead className="text-right">Por pagar</TableHead>
                    <TableHead>Estado</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {c.installments.map((i) => (
                    <TableRow key={i.id}>
                      <TableCell className="w-8 text-center">
                        {installmentGlyph(i.status, parseFloat(i.mora_amount) > 0)}
                      </TableCell>
                      <TableCell>{i.number}</TableCell>
                      <TableCell>{i.due_date}</TableCell>
                      <TableCell className="text-right">{i.paid_amount}</TableCell>
                      <TableCell className="text-right font-medium">
                        {i.status !== "PAID" ? i.total_due : "—"}
                        {parseFloat(i.mora_amount) > 0 && i.status !== "PAID" && (
                          <span className="ml-1 text-xs text-destructive">⚡</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {i.status === "PAID"
                          ? "Pagada"
                          : i.status === "OVERDUE"
                            ? "Vencida"
                            : i.status === "PARTIALLY_PAID"
                              ? `Parcial (debe S/ ${i.remaining_amount})`
                              : "Pendiente"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {history.length > 0 && (
                <p className="text-xs text-muted-foreground">
                  Has realizado pagos en {history.length} de tus cuotas. Cada
                  pago queda registrado con su método y fecha.
                </p>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
