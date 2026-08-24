"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  INSTALLMENT_STATUS_LABELS,
  PAYMENT_METHODS,
  fetchInstallments,
  payInstallment,
} from "@/lib/credits-api";
import { getErrorMessage, isForbidden } from "@/lib/api";
import { useAuth } from "@/hooks/use-auth";
import { RequireSection } from "@/components/guards";

const STATUS_BADGE: Record<string, "secondary" | "success" | "destructive"> = {
  PENDING: "secondary",
  PARTIALLY_PAID: "secondary",
  PAID: "success",
  OVERDUE: "destructive",
  RESTRUCTURED: "secondary",
};

const PAYABLE = ["PENDING", "PARTIALLY_PAID", "OVERDUE"];

export default function CuotasPage() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const canPay =
    (user?.is_superuser ?? false) ||
    (user?.permissions ?? []).includes("cuotas.gestionar");

  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);

  const [payTarget, setPayTarget] = useState<{
    id: string;
    agreementId: string;
    number: number;
    totalDue: string;
    mora: string;
    remaining: string;
    paid: string;
  } | null>(null);
  const [payAmount, setPayAmount] = useState("");
  const [payMethod, setPayMethod] = useState("CASH");

  const installmentsQuery = useQuery({
    queryKey: ["installments", status, page],
    queryFn: () =>
      fetchInstallments({
        status: status || undefined,
        page,
        per_page: 20,
      }),
  });

  useEffect(() => {
    if (isForbidden(installmentsQuery.error)) setForbidden(true);
    else if (installmentsQuery.error)
      setError(getErrorMessage(installmentsQuery.error));
  }, [installmentsQuery.error]);

  const payMutation = useMutation({
    mutationFn: () =>
      payInstallment(payTarget!.id, { amount: payAmount, method: payMethod }),
    onSuccess: () => {
      setPayTarget(null);
      void queryClient.invalidateQueries({ queryKey: ["installments"] });
      void queryClient.invalidateQueries({ queryKey: ["credits"] });
    },
    onError: (e) => {
      if (isForbidden(e)) setForbidden(true);
      setError(getErrorMessage(e));
    },
  });

  if (forbidden) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-destructive">
          No tienes permisos para ver cuotas.
        </CardContent>
      </Card>
    );
  }

  const totalPages = Math.max(
    1,
    Math.ceil((installmentsQuery.data?.total ?? 0) / 20)
  );

  return (
    <RequireSection section="cuotas">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Cuotas</h1>
            <p className="text-sm text-muted-foreground">
              {installmentsQuery.data?.total ?? 0} cuotas
            </p>
          </div>
        </div>

        {error && (
          <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}

        <div className="flex flex-wrap gap-3">
          <Select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
          >
            <option value="">Todos los estados</option>
            {Object.entries(INSTALLMENT_STATUS_LABELS).map(([key, label]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </Select>
        </div>

        <Card>
          <CardContent className="p-0">
            {installmentsQuery.isLoading ? (
              <div className="flex justify-center py-10">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Crédito</TableHead>
                    <TableHead>#</TableHead>
                    <TableHead>Vencimiento</TableHead>
                    <TableHead className="text-right">Pagado</TableHead>
                    <TableHead className="text-right">Mora</TableHead>
                    <TableHead className="text-right">Por pagar</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(installmentsQuery.data?.items ?? []).map((i) => (
                    <TableRow key={i.id}>
                      <TableCell className="font-medium">
                        <Link
                          href={`/admin/creditos/${i.agreement_id}`}
                          className="underline"
                        >
                          Ver crédito
                        </Link>
                      </TableCell>
                      <TableCell>{i.number}</TableCell>
                      <TableCell>{i.due_date}</TableCell>
                      <TableCell className="text-right">{i.paid_amount}</TableCell>
                      <TableCell
                        className={`text-right ${
                          parseFloat(i.mora_amount) > 0
                            ? "font-medium text-destructive"
                            : ""
                        }`}
                      >
                        {i.mora_amount}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {i.total_due}
                      </TableCell>
                      <TableCell>
                        <Badge variant={STATUS_BADGE[i.status] ?? "secondary"}>
                          {(STATUS_BADGE[i.status] === "success" ? "✅ " : "") +
                            (INSTALLMENT_STATUS_LABELS[i.status] ?? i.status)}
                        </Badge>
                        {parseFloat(i.paid_amount) > 0 &&
                          i.status !== "PAID" && (
                            <span className="ml-1 text-xs text-muted-foreground">
                              ◐
                            </span>
                          )}
                      </TableCell>
                      <TableCell className="text-right">
                        {canPay && PAYABLE.includes(i.status) && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setPayTarget({
                                id: i.id,
                                agreementId: i.agreement_id,
                                number: i.number,
                                totalDue: i.total_due,
                                mora: i.mora_amount,
                                remaining: i.remaining_amount,
                                paid: i.paid_amount,
                              });
                              setPayAmount(i.total_due);
                              setPayMethod("CASH");
                              setError(null);
                            }}
                          >
                            Pagar
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Página {page} de {totalPages}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              Anterior
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Siguiente
            </Button>
          </div>
        </div>

        {/* Modal de pago */}
        <Dialog open={payTarget !== null} onOpenChange={(o) => !o && setPayTarget(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Pagar cuota #{payTarget?.number}</DialogTitle>
              <DialogDescription>
                Capital S/ {payTarget?.remaining} + mora S/ {payTarget?.mora} · ya
                pagado S/ {payTarget?.paid}. Pagos parciales permitidos.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="amount">Monto (S/)</Label>
                <Input
                  id="amount"
                  type="number"
                  min={0.01}
                  step="0.01"
                  value={payAmount}
                  onChange={(e) => setPayAmount(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="method">Método</Label>
                <Select
                  id="method"
                  value={payMethod}
                  onChange={(e) => setPayMethod(e.target.value)}
                >
                  {PAYMENT_METHODS.map((m) => (
                    <option key={m.value} value={m.value}>
                      {m.label}
                    </option>
                  ))}
                </Select>
              </div>
              <Button
                className="w-full"
                disabled={
                  payMutation.isPending || !(parseFloat(payAmount) > 0)
                }
                onClick={() => payMutation.mutate()}
              >
                {payMutation.isPending && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                Confirmar pago
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </RequireSection>
  );
}
