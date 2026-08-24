"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Check, Loader2, Send, X } from "lucide-react";
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
  QUOTE_STATUS_BADGE,
  QUOTE_STATUS_LABELS,
  acceptQuote,
  convertQuote,
  fetchQuote,
  rejectQuote,
  sendQuote,
} from "@/lib/quotes-api";
import { getErrorMessage, isForbidden } from "@/lib/api";
import { RequireSection } from "@/components/guards";

export default function CotizacionDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();

  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);
  const [convertOpen, setConvertOpen] = useState(false);
  const [saleType, setSaleType] = useState<"CASH" | "CREDIT">("CASH");
  const [initialPayment, setInitialPayment] = useState("");
  const [installments, setInstallments] = useState("6");
  const [rejectOpen, setRejectOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState("");

  const quoteQuery = useQuery({
    queryKey: ["quote", params.id],
    queryFn: () => fetchQuote(params.id),
  });

  useEffect(() => {
    if (isForbidden(quoteQuery.error)) setForbidden(true);
    else if (quoteQuery.error) setError(getErrorMessage(quoteQuery.error));
  }, [quoteQuery.error]);

  const invalidate = () =>
    void queryClient.invalidateQueries({ queryKey: ["quote", params.id] });

  const onError = (e: unknown) => {
    if (isForbidden(e)) setForbidden(true);
    setError(getErrorMessage(e));
  };

  const sendMutation = useMutation({
    mutationFn: () => sendQuote(params.id),
    onSuccess: invalidate,
    onError,
  });
  const acceptMutation = useMutation({
    mutationFn: () => acceptQuote(params.id),
    onSuccess: invalidate,
    onError,
  });
  const rejectMutation = useMutation({
    mutationFn: () => rejectQuote(params.id, rejectReason || undefined),
    onSuccess: () => {
      setRejectOpen(false);
      invalidate();
    },
    onError,
  });
  const convertMutation = useMutation({
    mutationFn: () =>
      convertQuote(params.id, {
        sale_type: saleType,
        initial_payment:
          saleType === "CREDIT" ? initialPayment || undefined : undefined,
        number_of_installments:
          saleType === "CREDIT" ? Number(installments) || 1 : undefined,
      }),
    onSuccess: (sale) => router.push(`/admin/ventas/${sale.sale_id}`),
    onError,
  });

  if (forbidden) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-destructive">
          No tienes permisos para ver cotizaciones.
        </CardContent>
      </Card>
    );
  }

  const quote = quoteQuery.data;
  const status = quote?.status ?? "";
  const canEdit = status === "DRAFT";
  const canRespond = status === "SENT" || status === "VIEWED";
  const canConvert = status === "ACCEPTED";

  return (
    <RequireSection section="cotizaciones">
      <div className="mx-auto max-w-4xl space-y-6">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" asChild>
            <Link href="/admin/cotizaciones">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <div className="flex flex-1 items-center gap-3">
            <h1 className="text-2xl font-semibold">{quote?.code ?? "…"}</h1>
            {quote && (
              <Badge variant={QUOTE_STATUS_BADGE[status] ?? "secondary"}>
                {QUOTE_STATUS_LABELS[status] ?? status}
              </Badge>
            )}
          </div>
          <div className="flex gap-2">
            {canEdit && (
              <Button
                variant="outline"
                onClick={() => sendMutation.mutate()}
                disabled={sendMutation.isPending}
              >
                {sendMutation.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Send className="mr-2 h-4 w-4" />
                )}
                Enviar por WhatsApp
              </Button>
            )}
            {canRespond && (
              <>
                <Button
                  onClick={() => acceptMutation.mutate()}
                  disabled={acceptMutation.isPending}
                >
                  <Check className="mr-2 h-4 w-4" /> Aceptar
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => setRejectOpen(true)}
                >
                  <X className="mr-2 h-4 w-4" /> Rechazar
                </Button>
              </>
            )}
            {canConvert && (
              <Button onClick={() => setConvertOpen(true)}>
                Convertir en venta
              </Button>
            )}
          </div>
        </div>

        {error && (
          <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Resumen</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-x-8 gap-y-2 text-sm sm:grid-cols-2">
            <p>
              <span className="text-muted-foreground">Cliente:</span>{" "}
              {quote?.customer_name ?? "—"}
            </p>
            <p>
              <span className="text-muted-foreground">Válida hasta:</span>{" "}
              {quote &&
                new Date(quote.valid_until).toLocaleDateString("es-PE")}
            </p>
            <p>
              <span className="text-muted-foreground">WhatsApp:</span>{" "}
              {quote?.sent_via_whatsapp ? "Enviado" : "No enviado"}
            </p>
            <p>
              <span className="text-muted-foreground">Total:</span> S/{" "}
              <span className="text-lg font-semibold">{quote?.total}</span>
            </p>
            {quote?.notes && (
              <p className="sm:col-span-2 whitespace-pre-line">
                <span className="text-muted-foreground">Notas:</span>{" "}
                {quote.notes}
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Ítems</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Producto</TableHead>
                  <TableHead className="text-right">Cantidad</TableHead>
                  <TableHead className="text-right">Precio</TableHead>
                  <TableHead className="text-right">Descuento</TableHead>
                  <TableHead className="text-right">Subtotal</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(quote?.items ?? []).map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>{item.product_name ?? "—"}</TableCell>
                    <TableCell className="text-right">{item.quantity}</TableCell>
                    <TableCell className="text-right">
                      S/ {item.unit_price}
                    </TableCell>
                    <TableCell className="text-right">
                      S/ {item.discount_amount}
                    </TableCell>
                    <TableCell className="text-right">
                      S/ {item.subtotal}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Diálogo de conversión */}
        <Dialog open={convertOpen} onOpenChange={setConvertOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Convertir en venta</DialogTitle>
              <DialogDescription>
                Se usan los precios congelados de la cotización. La operación es
                atómica.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="conv-tipo">Tipo de venta</Label>
                <Select
                  id="conv-tipo"
                  value={saleType}
                  onChange={(e) =>
                    setSaleType(e.target.value as "CASH" | "CREDIT")
                  }
                >
                  <option value="CASH">Contado</option>
                  <option value="CREDIT">Crédito</option>
                </Select>
              </div>
              {saleType === "CREDIT" && (
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <Label htmlFor="conv-inicial">Pago inicial (S/)</Label>
                    <Input
                      id="conv-inicial"
                      type="number"
                      min="0"
                      step="0.01"
                      value={initialPayment}
                      onChange={(e) => setInitialPayment(e.target.value)}
                      placeholder="0.00"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="conv-cuotas">N° de cuotas</Label>
                    <Input
                      id="conv-cuotas"
                      type="number"
                      min="1"
                      value={installments}
                      onChange={(e) => setInstallments(e.target.value)}
                    />
                  </div>
                </div>
              )}
              {error && (
                <p className="text-sm text-destructive">{error}</p>
              )}
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() => setConvertOpen(false)}
                >
                  Cancelar
                </Button>
                <Button
                  onClick={() => convertMutation.mutate()}
                  disabled={convertMutation.isPending}
                >
                  {convertMutation.isPending && (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  )}
                  Confirmar conversión
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Diálogo de rechazo */}
        <Dialog open={rejectOpen} onOpenChange={setRejectOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Rechazar cotización</DialogTitle>
              <DialogDescription>
                Motivo opcional que se registra en la cotización.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="rej-motivo">Motivo</Label>
                <Input
                  id="rej-motivo"
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  placeholder="Ej. Precios fuera de presupuesto"
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setRejectOpen(false)}>
                  Cancelar
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => rejectMutation.mutate()}
                  disabled={rejectMutation.isPending}
                >
                  Rechazar
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </RequireSection>
  );
}
