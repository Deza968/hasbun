"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AlertTriangle, Loader2, Plus, ShieldAlert, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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
  PAYMENT_METHODS,
  createCredit,
  searchCustomers,
  validateCredit,
} from "@/lib/credits-api";
import { fetchProducts } from "@/lib/catalog-api";
import { getErrorMessage } from "@/lib/api";
import type { CreditBlocker } from "@/lib/types";

interface ItemRow {
  product_id: string;
  sku: string;
  name: string;
  price: number;
  quantity: number;
}

function addMonths(iso: string, months: number): string {
  const d = new Date(`${iso}T00:00:00`);
  const day = d.getDate();
  d.setMonth(d.getMonth() + months);
  if (d.getDate() !== day) d.setDate(0);
  return d.toISOString().slice(0, 10);
}

function money(n: number): string {
  return (Math.round(n * 100) / 100).toFixed(2);
}

export default function NuevoCreditoPage() {
  const router = useRouter();

  const [customerId, setCustomerId] = useState("");
  const [items, setItems] = useState<ItemRow[]>([]);
  const [initialPayment, setInitialPayment] = useState("0");
  const [nInstallments, setNInstallments] = useState("3");
  const [ratePercent, setRatePercent] = useState("0");
  const [freeMonths, setFreeMonths] = useState("0");
  const [firstDue, setFirstDue] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 30);
    return d.toISOString().slice(0, 10);
  });
  const [initialMethod, setInitialMethod] = useState("CASH");
  const [productSearch, setProductSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const t = window.setTimeout(() => setDebouncedSearch(productSearch), 300);
    return () => window.clearTimeout(t);
  }, [productSearch]);

  const customersQuery = useQuery({
    queryKey: ["customers-options"],
    queryFn: () => searchCustomers({ per_page: 200 }),
  });

  const productsQuery = useQuery({
    queryKey: ["products-search", debouncedSearch],
    queryFn: () =>
      fetchProducts({
        search: debouncedSearch || undefined,
        active: true,
        admin: true,
        per_page: 8,
      }),
    enabled: true,
  });

  const total = items.reduce((acc, i) => acc + i.price * i.quantity, 0);
  const n = Math.max(1, parseInt(nInstallments) || 1);
  const rate = Math.max(0, parseFloat(ratePercent) || 0) / 100;

  const validateMutation = useMutation({
    mutationFn: () =>
      validateCredit({
        customer_id: customerId,
        total_amount: total.toFixed(2),
        initial_payment: initialPayment || "0",
        number_of_installments: n,
      }),
    onError: (e) => setError(getErrorMessage(e)),
  });

  // verificación en tiempo real (#F05-12)
  useEffect(() => {
    if (!customerId || total <= 0 || !validateMutation.isIdle) {
      return;
    }
    const t = window.setTimeout(() => validateMutation.mutate(), 400);
    return () => window.clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [customerId, total, initialPayment, n]);

  // preview del calendario (espejo de _build_installments del backend)
  const preview = useMemo(() => {
    const financed = Math.max(0, total - (parseFloat(initialPayment) || 0));
    const free = parseInt(freeMonths) || 0;
    const base = money(financed / n);
    let accumulated = 0;
    const rows: { number: number; due_date: string; amount: string }[] = [];
    for (let i = 1; i <= n; i++) {
      let amt = base;
      if (i === n) {
        amt = money(financed - accumulated);
      } else {
        accumulated += parseFloat(base);
      }
      if (i > free && rate > 0) {
        amt = money(parseFloat(amt) + financed * rate);
      }
      rows.push({ number: i, due_date: addMonths(firstDue, i - 1), amount: amt });
    }
    return rows;
  }, [total, initialPayment, n, rate, freeMonths, firstDue]);

  const createMutation = useMutation({
    mutationFn: () =>
      createCredit({
        customer_id: customerId,
        total_amount: total.toFixed(2),
        initial_payment: initialPayment || "0",
        number_of_installments: n,
        items: items.map((i) => ({
          product_id: i.product_id,
          quantity: String(i.quantity),
        })),
        interest_rate: String(rate),
        interest_free_months: parseInt(freeMonths) || 0,
        currency: "PEN",
        first_due_date: firstDue,
        initial_method: initialMethod,
      }),
    onSuccess: (credit) => router.push(`/admin/creditos/${credit.id}`),
    onError: (e) => setError(getErrorMessage(e)),
  });

  const validation = validateMutation.data;
  const blocked = validation ? !validation.approved : false;
  const canSubmit =
    customerId &&
    items.length > 0 &&
    total > 0 &&
    validation?.approved &&
    !createMutation.isPending;

  const renderBlockers = (
    list: CreditBlocker[],
    tone: "destructive" | "warning"
  ) => (
    <div className="space-y-2">
      {list.map((b, idx) => (
        <div
          key={idx}
          className={`flex items-start gap-2 rounded-md px-3 py-2 text-sm ${
            tone === "destructive"
              ? "bg-destructive/10 text-destructive"
              : "bg-amber-500/10 text-amber-700 dark:text-amber-400"
          }`}
        >
          {tone === "destructive" ? (
            <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" />
          ) : (
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          )}
          <span>
            <strong>{b.authorization}</strong>: {b.message}
          </span>
        </div>
      ))}
    </div>
  );

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Nuevo crédito</h1>
        <p className="text-sm text-muted-foreground">
          Venta a crédito con cuotas, validación previa y reserva de stock.
        </p>
      </div>

      {error && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Cliente</CardTitle>
        </CardHeader>
        <CardContent>
          <Select
            value={customerId}
            onChange={(e) => {
              setCustomerId(e.target.value);
              validateMutation.reset();
            }}
          >
            <option value="">Seleccionar cliente…</option>
            {(customersQuery.data?.items ?? []).map((c) => (
              <option key={c.id} value={c.id}>
                {(c.razon_social ??
                  `${c.first_name ?? ""} ${c.last_name ?? ""}`.trim()) +
                  ` — límite S/ ${c.credit_limit}`}
                {c.is_frequent ? " (frecuente)" : ""}
              </option>
            ))}
          </Select>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Productos</CardTitle>
          <CardDescription>
            El monto se calcula con el precio vigente de cada producto.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            placeholder="Buscar producto por nombre o SKU…"
            value={productSearch}
            onChange={(e) => setProductSearch(e.target.value)}
          />
          {debouncedSearch && (productsQuery.data?.items?.length ?? 0) > 0 && (
            <div className="divide-y rounded-md border">
              {(productsQuery.data?.items ?? [])
                .filter((p) => !items.some((i) => i.product_id === p.id))
                .map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-muted/50"
                    onClick={() => {
                      setItems((prev) => [
                        ...prev,
                        {
                          product_id: p.id,
                          sku: p.sku,
                          name: p.name,
                          price: parseFloat(p.sale_price),
                          quantity: 1,
                        },
                      ]);
                      setProductSearch("");
                      validateMutation.reset();
                    }}
                  >
                    <span>
                      <span className="font-medium">{p.name}</span>{" "}
                      <span className="text-xs text-muted-foreground">
                        {p.sku}
                      </span>
                    </span>
                    <span className="text-sm">S/ {p.sale_price}</span>
                  </button>
                ))}
            </div>
          )}

          {items.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Producto</TableHead>
                  <TableHead className="w-24 text-right">Cantidad</TableHead>
                  <TableHead className="text-right">Precio</TableHead>
                  <TableHead className="text-right">Subtotal</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((i) => (
                  <TableRow key={i.product_id}>
                    <TableCell>
                      <span className="font-medium">{i.name}</span>{" "}
                      <span className="text-xs text-muted-foreground">
                        {i.sku}
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      <Input
                        type="number"
                        min={1}
                        value={i.quantity}
                        onChange={(e) => {
                          const q = Math.max(1, parseInt(e.target.value) || 1);
                          setItems((prev) =>
                            prev.map((it) =>
                              it.product_id === i.product_id
                                ? { ...it, quantity: q }
                                : it
                            )
                          );
                        }}
                        className="ml-auto h-8 w-20 text-right"
                      />
                    </TableCell>
                    <TableCell className="text-right">{money(i.price)}</TableCell>
                    <TableCell className="text-right">
                      {money(i.price * i.quantity)}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() =>
                          setItems((prev) =>
                            prev.filter((it) => it.product_id !== i.product_id)
                          )
                        }
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
          <p className="text-right text-sm font-medium">
            Total: <span className="text-lg">S/ {money(total)}</span>
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Condiciones del crédito</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-3">
          <div className="space-y-2">
            <Label htmlFor="initial">Pago inicial (S/)</Label>
            <Input
              id="initial"
              type="number"
              min={0}
              step="0.01"
              value={initialPayment}
              onChange={(e) => setInitialPayment(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="method">Método del inicial</Label>
            <Select
              id="method"
              value={initialMethod}
              onChange={(e) => setInitialMethod(e.target.value)}
            >
              {PAYMENT_METHODS.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label}
                </option>
              ))}
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="n">Número de cuotas</Label>
            <Input
              id="n"
              type="number"
              min={1}
              max={60}
              value={nInstallments}
              onChange={(e) => setNInstallments(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="rate">Tasa mensual (%)</Label>
            <Input
              id="rate"
              type="number"
              min={0}
              step="0.01"
              value={ratePercent}
              onChange={(e) => setRatePercent(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="free">Meses sin interés</Label>
            <Input
              id="free"
              type="number"
              min={0}
              value={freeMonths}
              onChange={(e) => setFreeMonths(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="firstdue">Primera cuota</Label>
            <Input
              id="firstdue"
              type="date"
              value={firstDue}
              onChange={(e) => setFirstDue(e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      {validateMutation.isPending && (
        <p className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" /> Verificando reglas de crédito…
        </p>
      )}

      {validation && validation.blockers.length > 0 && (
        <div className="space-y-2">{renderBlockers(validation.blockers, "destructive")}</div>
      )}
      {validation && validation.warnings.length > 0 && (
        <div className="space-y-2">{renderBlockers(validation.warnings, "warning")}</div>
      )}
      {validation?.approved && (
        <Badge variant="success">Verificación aprobada — puede registrar el crédito</Badge>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Calendario referencial de cuotas</CardTitle>
          <CardDescription>
            Vista previa; el backend calcula los montos finales.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>#</TableHead>
                <TableHead>Vencimiento</TableHead>
                <TableHead className="text-right">Monto (S/)</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {preview.map((r) => (
                <TableRow key={r.number}>
                  <TableCell>{r.number}</TableCell>
                  <TableCell>{r.due_date}</TableCell>
                  <TableCell className="text-right">{r.amount}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <div className="flex justify-end gap-3">
        <Button variant="outline" onClick={() => router.back()}>
          Cancelar
        </Button>
        <Button disabled={!canSubmit} onClick={() => createMutation.mutate()}>
          {createMutation.isPending && (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          )}
          <Plus className="mr-2 h-4 w-4" /> Registrar crédito
        </Button>
      </div>
    </div>
  );
}
