"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Loader2, Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
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
  createQuote,
  searchCustomersForQuote,
  searchProductsForQuote,
} from "@/lib/quotes-api";
import { getErrorMessage } from "@/lib/api";
import { RequireSection } from "@/components/guards";

interface LineItem {
  product_id: string;
  name: string;
  quantity: string;
  unit_price: string;
  discount_amount: string;
}

export default function NuevaCotizacionPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [customerId, setCustomerId] = useState("");
  const [validUntil, setValidUntil] = useState("");
  const [notes, setNotes] = useState("");
  const [items, setItems] = useState<LineItem[]>([]);

  const customersQuery = useQuery({
    queryKey: ["quote-customers"],
    queryFn: searchCustomersForQuote,
  });
  const productsQuery = useQuery({
    queryKey: ["quote-products"],
    queryFn: () => searchProductsForQuote(),
  });

  const total = useMemo(
    () =>
      items
        .reduce(
          (acc, it) =>
            acc +
            Number(it.quantity || 0) * Number(it.unit_price || 0) -
            Number(it.discount_amount || 0),
          0
        )
        .toFixed(2),
    [items]
  );

  const addProduct = (productId: string) => {
    if (!productId) return;
    const product = productsQuery.data?.items.find((p) => p.id === productId);
    if (!product) return;
    setItems((prev) => [
      ...prev.filter((i) => i.product_id !== productId),
      {
        product_id: productId,
        name: product.name,
        quantity: "1",
        unit_price: String(product.sale_price),
        discount_amount: "0",
      },
    ]);
  };

  const updateItem = (productId: string, field: keyof LineItem, value: string) =>
    setItems((prev) =>
      prev.map((i) => (i.product_id === productId ? { ...i, [field]: value } : i))
    );

  const createMutation = useMutation({
    mutationFn: () =>
      createQuote({
        customer_id: customerId,
        valid_until: validUntil,
        notes: notes || undefined,
        items: items.map((i) => ({
          product_id: i.product_id,
          quantity: i.quantity,
          unit_price: i.unit_price,
          discount_amount: i.discount_amount || undefined,
        })),
      }),
    onSuccess: (quote) => router.push(`/admin/cotizaciones/${quote.id}`),
    onError: (e) => setError(getErrorMessage(e)),
  });

  const submit = () => {
    setError(null);
    if (!customerId) return setError("Selecciona un cliente");
    if (!validUntil) return setError("Indica la fecha de vigencia");
    if (new Date(validUntil) < new Date(new Date().toDateString()))
      return setError("La vigencia debe ser hoy o futura");
    if (items.length === 0) return setError("Agrega al menos un producto");
    createMutation.mutate();
  };

  return (
    <RequireSection section="cotizaciones">
      <div className="mx-auto max-w-4xl space-y-6">
        <h1 className="text-2xl font-semibold">Nueva cotización</h1>
        {error && (
          <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Datos generales</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-3">
            <div className="space-y-1.5">
              <Label>Cliente</Label>
              <Select
                value={customerId}
                onChange={(e) => setCustomerId(e.target.value)}
              >
                <option value="">Seleccionar…</option>
                {(customersQuery.data?.items ?? []).map((c) => (
                  <option key={c.id} value={c.id}>
                    {[c.first_name, c.last_name].filter(Boolean).join(" ") ||
                      c.razon_social}
                  </option>
                ))}
              </Select>
            </div>
            <div className="space-y-1.5">
              <label htmlFor="cot-vigencia" className="text-sm font-medium">Válida hasta</label>
              <Input
                id="cot-vigencia"
                type="date"
                value={validUntil}
                onChange={(e) => setValidUntil(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <label htmlFor="cot-notas" className="text-sm font-medium">Notas</label>
              <Input
                id="cot-notas"
                placeholder="Opcional"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Productos</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Select value="" onChange={(e) => addProduct(e.target.value)}>
              <option value="">+ Agregar producto…</option>
              {(productsQuery.data?.items ?? []).map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} — S/ {p.sale_price}
                </option>
              ))}
            </Select>

            {items.length > 0 && (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Producto</TableHead>
                    <TableHead className="w-24 text-right">Cant.</TableHead>
                    <TableHead className="w-32 text-right">Precio</TableHead>
                    <TableHead className="w-28 text-right">Desc.</TableHead>
                    <TableHead className="w-24" />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((item) => (
                    <TableRow key={item.product_id}>
                      <TableCell>{item.name}</TableCell>
                      <TableCell className="text-right">
                        <Input
                          aria-label={`Cantidad ${item.name}`}
                          type="number"
                          min="0"
                          step="1"
                          value={item.quantity}
                          onChange={(e) =>
                            updateItem(item.product_id, "quantity", e.target.value)
                          }
                          className="w-20 text-right"
                        />
                      </TableCell>
                      <TableCell className="text-right">
                        <Input
                          aria-label={`Precio ${item.name}`}
                          type="number"
                          min="0"
                          step="0.01"
                          value={item.unit_price}
                          onChange={(e) =>
                            updateItem(item.product_id, "unit_price", e.target.value)
                          }
                          className="w-28 text-right"
                        />
                      </TableCell>
                      <TableCell className="text-right">
                        <Input
                          aria-label={`Descuento ${item.name}`}
                          type="number"
                          min="0"
                          step="0.01"
                          value={item.discount_amount}
                          onChange={(e) =>
                            updateItem(item.product_id, "discount_amount", e.target.value)
                          }
                          className="w-24 text-right"
                        />
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() =>
                            setItems((prev) =>
                              prev.filter((i) => i.product_id !== item.product_id)
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

            <div className="flex items-center justify-between border-t pt-4">
              <p className="text-sm text-muted-foreground">
                Los precios quedan congelados al crear la cotización.
              </p>
              <p className="text-lg font-semibold">Total: S/ {total}</p>
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-end gap-2">
          <Button
            variant="outline"
            onClick={() => router.push("/admin/cotizaciones")}
          >
            Cancelar
          </Button>
          <Button onClick={submit} disabled={createMutation.isPending}>
            {createMutation.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            <Plus className="mr-2 h-4 w-4" /> Crear cotización
          </Button>
        </div>
      </div>
    </RequireSection>
  );
}
