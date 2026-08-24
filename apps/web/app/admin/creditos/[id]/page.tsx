"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Loader2, Truck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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
  AGREEMENT_STATUS_BADGE,
  AGREEMENT_STATUS_LABELS,
  INSTALLMENT_STATUS_LABELS,
  PAYMENT_METHODS,
  deliverCredit,
  fetchCredit,
  payInstallment,
  payMultiple,
  restructureInstallment,
} from "@/lib/credits-api";
import { getErrorMessage, isForbidden } from "@/lib/api";
import { useAuth } from "@/hooks/use-auth";
import { RequireSection } from "@/components/guards";

export default function CreditoDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const isOwner = user?.is_superuser ?? false;
  const canDeliver =
    isOwner || (user?.permissions ?? []).includes("creditos.aprobar");
  const canPay = isOwner || (user?.permissions ?? []).includes("cuotas.gestionar");

  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);
  const [payTarget, setPayTarget] = useState<{ id: string; totalDue: string; mora: string; remaining: string } | null>(null);
  const [payAmount, setPayAmount] = useState("");
  const [payMethod, setPayMethod] = useState("CASH");
  const [payReference, setPayReference] = useState("");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [multipleOpen, setMultipleOpen] = useState(false);
  const [multipleAmount, setMultipleAmount] = useState("");
  const [restructureTarget, setRestructureTarget] = useState<{ id: string } | null>(null);
  const [newDue, setNewDue] = useState("");
  const [reason, setReason] = useState("");

  const creditQuery = useQuery({
    queryKey: ["credit", params.id],
    queryFn: () => fetchCredit(params.id),
  });

  useEffect(() => {
    if (isForbidden(creditQuery.error)) setForbidden(true);
    else if (creditQuery.error) setError(getErrorMessage(creditQuery.error));
  }, [creditQuery.error]);

  const invalidate = () =>
    void queryClient.invalidateQueries({ queryKey: ["credit", params.id] });

  const onError = (e: unknown) => {
    if (isForbidden(e)) setForbidden(true);
    setError(getErrorMessage(e));
  };

  const payMutation = useMutation({
    mutationFn: () =>
      payInstallment(payTarget!.id, {
        amount: payAmount,
        method: payMethod,
        reference: payReference || undefined,
      }),
    onSuccess: () => {
      closePay();
      invalidate();
    },
    onError,
  });

  const multipleMutation = useMutation({
    mutationFn: () =>
      payMultiple(params.id, {
        installment_ids: selectedIds,
        amount: multipleAmount,
        method: payMethod,
      }),
    onSuccess: () => {
      setMultipleOpen(false);
      setSelectedIds([]);
      setMultipleAmount("");
      invalidate();
    },
    onError,
  });

  const restructureMutation = useMutation({
    mutationFn: () =>
      restructureInstallment(restructureTarget!.id, {
        new_due_date: newDue,
        reason,
      }),
    onSuccess: () => {
      setRestructureTarget(null);
      setNewDue("");
      setReason("");
      invalidate();
    },
    onError,
  });

  const deliverMutation = useMutation({
    mutationFn: () => deliverCredit(params.id),
    onSuccess: invalidate,
    onError,
  });

  function openPay(inst: { id: string; total_due: string; mora_amount: string; remaining_amount: string }) {
    setPayTarget({
      id: inst.id,
      totalDue: inst.total_due,
      mora: inst.mora_amount,
      remaining: inst.remaining_amount,
    });
    setPayAmount(inst.total_due);
    setPayMethod("CASH");
    setPayReference("");
    setError(null);
  }

  function closePay() {
    setPayTarget(null);
    setError(null);
  }

  if (forbidden) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-destructive">
          No tienes permisos para ver créditos.
        </CardContent>
      </Card>
    );
  }

  if (creditQuery.isLoading) {
    return (
      <div className="flex justify-center py-10">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const c = creditQuery.data;
  if (!c) return null;

  const toggleSelected = (id: string) =>
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );

  const payableStatuses = ["PENDING", "PARTIALLY_PAID", "OVERDUE"];
  const selectable = c.installments.filter((i) =>
    payableStatuses.includes(i.status)
  );

  return (
    <RequireSection section="creditos">
      <div className="mx-auto max-w-5xl space-y-6">
        <Button variant="ghost" size="sm" onClick={() => router.back()}>
          <ArrowLeft className="mr-2 h-4 w-4" /> Volver
        </Button>

        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold">{c.code}</h1>
            <p className="text-sm text-muted-foreground">
              Creado el {new Date(c.created_at).toLocaleDateString("es-PE")}
            </p>
          </div>
          <Badge variant={AGREEMENT_STATUS_BADGE[c.status] ?? "secondary"}>
            {AGREEMENT_STATUS_LABELS[c.status] ?? c.status}
          </Badge>
        </div>

        {error && (
          <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}

        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Cuotas</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    {canPay && <TableHead className="w-8" />}
                    <TableHead>#</TableHead>
                    <TableHead>Vencimiento</TableHead>
                    <TableHead className="text-right">Capital</TableHead>
                    <TableHead className="text-right">Mora</TableHead>
                    <TableHead className="text-right">Por pagar</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {c.installments.map((i) => (
                    <TableRow key={i.id}>
                      {canPay && (
                        <TableCell>
                          <input
                            type="checkbox"
                            disabled={!payableStatuses.includes(i.status)}
                            checked={selectedIds.includes(i.id)}
                            onChange={() => toggleSelected(i.id)}
                            aria-label={`Seleccionar cuota ${i.number}`}
                          />
                        </TableCell>
                      )}
                      <TableCell>{i.number}</TableCell>
                      <TableCell>
                        {i.due_date}
                        {i.original_due_date && i.original_due_date !== i.due_date && (
                          <span className="ml-1 text-xs text-muted-foreground">
                            (orig. {i.original_due_date})
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        {i.remaining_amount}
                      </TableCell>
                      <TableCell
                        className={`text-right ${
                          parseFloat(i.mora_amount) > 0 ? "font-medium text-destructive" : ""
                        }`}
                      >
                        {i.mora_amount}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {i.total_due}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            i.status === "PAID"
                              ? "success"
                              : i.status === "OVERDUE"
                                ? "destructive"
                                : "secondary"
                          }
                        >
                          {INSTALLMENT_STATUS_LABELS[i.status] ?? i.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="space-x-1 text-right">
                        {canPay && payableStatuses.includes(i.status) && (
                          <Button variant="ghost" size="sm" onClick={() => openPay(i)}>
                            Pagar
                          </Button>
                        )}
                        {isOwner && i.status !== "PAID" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setRestructureTarget({ id: i.id });
                              setNewDue(i.due_date);
                              setReason("");
                            }}
                          >
                            Reprogramar
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Resumen</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Total</span>
                  <span>S/ {c.total_amount}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Inicial</span>
                  <span>S/ {c.initial_payment}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Financiado</span>
                  <span>S/ {c.financed_amount}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Cuotas</span>
                  <span>{c.number_of_installments} × S/ {c.installment_amount}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Tasa mensual</span>
                  <span>
                    {(parseFloat(c.interest_rate) * 100).toFixed(2)}% ({c.interest_free_months} meses sin interés)
                  </span>
                </div>
                <div className="flex justify-between border-t pt-2">
                  <span className="text-muted-foreground">Primera cuota</span>
                  <span>{c.first_due_date}</span>
                </div>
              </CardContent>
            </Card>

            {canDeliver && (c.status === "ACTIVE" || c.status === "APPROVED") && (
              <Card>
                <CardHeader>
                  <CardTitle>Entrega anticipada</CardTitle>
                </CardHeader>
                <CardContent>
                  <Button
                    className="w-full"
                    onClick={() => deliverMutation.mutate()}
                    disabled={deliverMutation.isPending}
                  >
                    {deliverMutation.isPending && (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    )}
                    <Truck className="mr-2 h-4 w-4" /> Entregar al cliente
                  </Button>
                </CardContent>
              </Card>
            )}

            <Card>
              <CardContent className="pt-6 text-sm">
                <Link href={`/admin/ventas/${c.sale_id}`} className="underline">
                  Ver venta asociada
                </Link>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Pago de cuota */}
        <Dialog open={payTarget !== null} onOpenChange={(o) => !o && closePay()}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Pagar cuota</DialogTitle>
              <DialogDescription>
                Capital S/ {payTarget?.remaining} + mora S/ {payTarget?.mora}. Se
                aceptan pagos parciales.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="payamount">Monto (S/)</Label>
                <Input
                  id="payamount"
                  type="number"
                  min={0.01}
                  step="0.01"
                  value={payAmount}
                  onChange={(e) => setPayAmount(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="paymethod">Método</Label>
                <Select
                  id="paymethod"
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
              <div className="space-y-2">
                <Label htmlFor="payref">Referencia (opcional)</Label>
                <Input
                  id="payref"
                  value={payReference}
                  onChange={(e) => setPayReference(e.target.value)}
                />
              </div>
              <Button
                className="w-full"
                disabled={payMutation.isPending || !(parseFloat(payAmount) > 0)}
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

        {/* Pago adelantado múltiple */}
        <Dialog open={multipleOpen} onOpenChange={setMultipleOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Pago adelantado ({selectedIds.length} cuotas)</DialogTitle>
              <DialogDescription>
                El monto se distribuye en orden desde la cuota más antigua.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="multamount">Monto total (S/)</Label>
                <Input
                  id="multamount"
                  type="number"
                  min={0.01}
                  step="0.01"
                  value={multipleAmount}
                  onChange={(e) => setMultipleAmount(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="multmethod">Método</Label>
                <Select
                  id="multmethod"
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
                  multipleMutation.isPending ||
                  selectedIds.length === 0 ||
                  !(parseFloat(multipleAmount) > 0)
                }
                onClick={() => multipleMutation.mutate()}
              >
                {multipleMutation.isPending && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                Aplicar pago adelantado
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Reprogramar cuota (OWNER) */}
        <Dialog
          open={restructureTarget !== null}
          onOpenChange={(o) => !o && setRestructureTarget(null)}
        >
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Reprogramar cuota</DialogTitle>
              <DialogDescription>
                Solo OWNER. La fecha original queda registrada.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="newdue">Nueva fecha de vencimiento</Label>
                <Input
                  id="newdue"
                  type="date"
                  value={newDue}
                  onChange={(e) => setNewDue(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="reason">Motivo</Label>
                <Input
                  id="reason"
                  placeholder="Mínimo 5 caracteres"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                />
              </div>
              <Button
                className="w-full"
                disabled={
                  restructureMutation.isPending || !newDue || reason.length < 5
                }
                onClick={() => restructureMutation.mutate()}
              >
                {restructureMutation.isPending && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                Reprogramar
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {canPay && selectedIds.length > 0 && (
          <div className="fixed bottom-6 right-6">
            <Button
              size="lg"
              onClick={() => {
                setMultipleAmount("");
                setMultipleOpen(true);
              }}
            >
              Pago adelantado · {selectedIds.length} cuotas
            </Button>
          </div>
        )}
      </div>
    </RequireSection>
  );
}
