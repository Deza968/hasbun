"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, ArrowLeft } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  cancelPurchase,
  confirmPurchase,
  fetchPurchase,
  receivePurchase,
} from "@/lib/inventory-api";
import { getErrorMessage, isForbidden } from "@/lib/api";
import { useAuth } from "@/hooks/use-auth";
import { RequireSection } from "@/components/guards";

const STATUS_LABELS: Record<string, string> = {
  DRAFT: "Borrador",
  ORDERED: "Pedido",
  PARTIAL: "Recepción parcial",
  RECEIVED: "Recibida",
  CANCELLED: "Cancelada",
};

const STATUS_BADGE: Record<string, "secondary" | "success" | "destructive"> = {
  DRAFT: "secondary",
  ORDERED: "secondary",
  PARTIAL: "secondary",
  RECEIVED: "success",
  CANCELLED: "destructive",
};

export default function CompraDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const isOwner = user?.is_superuser ?? false;

  const [received, setReceived] = useState<Record<string, string>>({});
  const [receiveOpen, setReceiveOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);

  const purchaseQuery = useQuery({
    queryKey: ["purchase", params.id],
    queryFn: () => fetchPurchase(params.id),
  });

  useEffect(() => {
    if (isForbidden(purchaseQuery.error)) setForbidden(true);
    else if (purchaseQuery.error)
      setError(getErrorMessage(purchaseQuery.error));
  }, [purchaseQuery.error]);

  const invalidate = () =>
    void queryClient.invalidateQueries({ queryKey: ["purchase", params.id] });

  const confirmMutation = useMutation({
    mutationFn: () => confirmPurchase(params.id),
    onSuccess: invalidate,
    onError: (e) => {
      if (isForbidden(e)) setForbidden(true);
      setError(getErrorMessage(e));
    },
  });

  const receiveMutation = useMutation({
    mutationFn: () =>
      receivePurchase(
        params.id,
        (purchaseQuery.data?.items ?? []).map((i) => ({
          item_id: i.id,
          received_quantity: received[i.id] ?? String(Number(i.quantity) - Number(i.received_quantity)),
        }))
      ),
    onSuccess: () => {
      setReceiveOpen(false);
      invalidate();
    },
    onError: (e) => {
      if (isForbidden(e)) setForbidden(true);
      setError(getErrorMessage(e));
    },
  });

  const cancelMutation = useMutation({
    mutationFn: () => cancelPurchase(params.id, cancelReason),
    onSuccess: () => {
      setCancelReason("");
      invalidate();
    },
    onError: (e) => {
      if (isForbidden(e)) setForbidden(true);
      setError(getErrorMessage(e));
    },
  });

  const p = purchaseQuery.data;

  if (forbidden) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-destructive">
          No tienes permisos para ver compras.
        </CardContent>
      </Card>
    );
  }

  const canReceive = p?.status === "ORDERED" || p?.status === "PARTIAL";

  return (
    <RequireSection section="compras">
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={() => router.back()}>
            <ArrowLeft className="mr-2 h-4 w-4" /> Volver
          </Button>
          <div className="flex-1">
            <h1 className="text-2xl font-semibold">{p?.code ?? "Compra"}</h1>
            <p className="text-sm text-muted-foreground">
              {p?.supplier_name ?? "—"} · {p ? new Date(p.created_at).toLocaleString("es-PE") : ""}
            </p>
          </div>
          {p && <Badge variant={STATUS_BADGE[p.status] ?? "secondary"}>{STATUS_LABELS[p.status] ?? p.status}</Badge>}
        </div>

        {error && (
          <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}

        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Ítems</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Producto</TableHead>
                    <TableHead className="text-right">Cantidad</TableHead>
                    <TableHead className="text-right">Recibido</TableHead>
                    <TableHead className="text-right">Costo unit.</TableHead>
                    <TableHead className="text-right">Subtotal</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(p?.items ?? []).map((i) => (
                    <TableRow key={i.id}>
                      <TableCell>
                        <p className="font-medium">{i.product_name}</p>
                        <p className="text-xs text-muted-foreground">{i.product_sku}</p>
                      </TableCell>
                      <TableCell className="text-right">{i.quantity}</TableCell>
                      <TableCell className="text-right">{i.received_quantity}</TableCell>
                      <TableCell className="text-right">{i.unit_cost}</TableCell>
                      <TableCell className="text-right">{i.subtotal}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Resumen</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Proveedor</span>
                <span>
                  {p?.supplier_name ? (
                    <Link
                      href={`/admin/proveedores/${p.supplier_id}`}
                      className="underline-offset-4 hover:underline"
                    >
                      {p.supplier_name}
                    </Link>
                  ) : (
                    "—"
                  )}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Moneda</span>
                <span>{p?.currency}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Tipo de cambio</span>
                <span>{p?.exchange_rate}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total</span>
                <span className="font-semibold">
                  {p?.total} {p?.currency}
                </span>
              </div>
              {p?.notes && (
                <div className="border-t pt-2 text-xs text-muted-foreground">
                  {p.notes}
                </div>
              )}

              {isOwner && p?.status === "DRAFT" && (
                <Button
                  className="w-full"
                  disabled={confirmMutation.isPending}
                  onClick={() => confirmMutation.mutate()}
                >
                  {confirmMutation.isPending ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : null}
                  Confirmar pedido
                </Button>
              )}

              {isOwner && canReceive && (
                <Button
                  className="w-full"
                  variant="secondary"
                  onClick={() => {
                    setReceived({});
                    setReceiveOpen(true);
                  }}
                >
                  Registrar recepción
                </Button>
              )}

              {isOwner && p?.status === "DRAFT" && (
                <>
                  <Input
                    placeholder="Motivo de cancelación..."
                    value={cancelReason}
                    onChange={(e) => setCancelReason(e.target.value)}
                  />
                  <Button
                    className="w-full"
                    variant="destructive"
                    disabled={cancelReason.trim().length < 5 || cancelMutation.isPending}
                    onClick={() => cancelMutation.mutate()}
                  >
                    Cancelar compra
                  </Button>
                </>
              )}
            </CardContent>
          </Card>
        </div>

        {receiveOpen && (
          <Card>
            <CardHeader>
              <CardTitle>Recepción de mercadería</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Producto</TableHead>
                    <TableHead className="text-right">Pedido</TableHead>
                    <TableHead className="text-right">Recibido antes</TableHead>
                    <TableHead className="w-32">Recibir ahora</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(p?.items ?? []).map((i) => (
                    <TableRow key={i.id}>
                      <TableCell>{i.product_name}</TableCell>
                      <TableCell className="text-right">{i.quantity}</TableCell>
                      <TableCell className="text-right">{i.received_quantity}</TableCell>
                      <TableCell>
                        <Input
                          type="number"
                          step="0.001"
                          min={0}
                          defaultValue={String(Number(i.quantity) - Number(i.received_quantity))}
                          onChange={(e) =>
                            setReceived((prev) => ({
                              ...prev,
                              [i.id]: e.target.value,
                            }))
                          }
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setReceiveOpen(false)}>
                  Cancelar
                </Button>
                <Button
                  disabled={receiveMutation.isPending}
                  onClick={() => receiveMutation.mutate()}
                >
                  {receiveMutation.isPending ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : null}
                  Confirmar recepción
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </RequireSection>
  );
}