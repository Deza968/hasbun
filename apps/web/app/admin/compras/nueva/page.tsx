"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { createPurchase, fetchSuppliers } from "@/lib/inventory-api";
import { fetchProducts } from "@/lib/catalog-api";
import { getErrorMessage, isForbidden } from "@/lib/api";
import { RequireSection } from "@/components/guards";

interface ItemLine {
  product_id: string;
  product_name: string;
  product_sku: string;
  quantity: string;
  unit_cost: string;
}

export default function NuevaCompraPage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const [supplierId, setSupplierId] = useState("");
  const [currency, setCurrency] = useState("PEN");
  const [exchangeRate, setExchangeRate] = useState("1");
  const [notes, setNotes] = useState("");
  const [items, setItems] = useState<ItemLine[]>([]);
  const [productSearch, setProductSearch] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);

  const suppliersQuery = useQuery({
    queryKey: ["suppliers"],
    queryFn: () => fetchSuppliers({ per_page: 100 }),
  });

  const productsQuery = useQuery({
    queryKey: ["products-search", productSearch],
    queryFn: () =>
      fetchProducts({ search: productSearch || undefined, page: 1, per_page: 10 }),
    enabled: productSearch.trim().length >= 2,
  });

  const addItem = (p: { id: string; name: string; sku: string }) => {
    setItems((prev) => {
      const existing = prev.find((i) => i.product_id === p.id);
      if (existing) {
        return prev.map((i) =>
          i.product_id === p.id
            ? { ...i, quantity: String(Number(i.quantity) + 1) }
            : i
        );
      }
      return [
        ...prev,
        {
          product_id: p.id,
          product_name: p.name,
          product_sku: p.sku,
          quantity: "1",
          unit_cost: "",
        },
      ];
    });
    setProductSearch("");
  };

  const total = useMemo(
    () =>
      items.reduce(
        (acc, i) => acc + (Number(i.quantity) || 0) * (Number(i.unit_cost) || 0),
        0
      ),
    [items]
  );

  const saveMutation = useMutation({
    mutationFn: () =>
      createPurchase({
        supplier_id: supplierId,
        currency,
        exchange_rate: exchangeRate,
        exchange_rate_source: "manual",
        notes: notes || null,
        items: items.map((i) => ({
          product_id: i.product_id,
          quantity: i.quantity,
          unit_cost: i.unit_cost,
        })),
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["purchases"] });
      router.push("/admin/compras");
    },
    onError: (e) => {
      if (isForbidden(e)) setForbidden(true);
      setError(getErrorMessage(e));
    },
  });

  const canSave =
    Boolean(supplierId) &&
    items.length > 0 &&
    items.every((i) => Number(i.quantity) > 0 && i.unit_cost !== "");

  if (forbidden) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-destructive">
          No tienes permisos para crear compras.
        </CardContent>
      </Card>
    );
  }

  return (
    <RequireSection section="compras">
      <div className="mx-auto max-w-4xl space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">Nueva compra</h1>
          <Button
            disabled={!canSave || saveMutation.isPending}
            onClick={() => saveMutation.mutate()}
          >
            {saveMutation.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : null}
            Crear compra
          </Button>
        </div>

        {error && (
          <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Datos de la orden</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="space-y-2">
                <Label>Proveedor *</Label>
                <Select value={supplierId} onChange={(e) => setSupplierId(e.target.value)}>
                  <option value="">Seleccionar...</option>
                  {(suppliersQuery.data?.items ?? []).map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.razon_social}
                    </option>
                  ))}
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Moneda</Label>
                <Select value={currency} onChange={(e) => setCurrency(e.target.value)}>
                  <option value="PEN">PEN</option>
                  <option value="USD">USD</option>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Tipo de cambio</Label>
                <Input
                  type="number"
                  step="0.0001"
                  value={exchangeRate}
                  onChange={(e) => setExchangeRate(e.target.value)}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Notas</Label>
              <textarea
                className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm"
                rows={2}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Productos</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Buscar producto</Label>
              <Input
                placeholder="Buscar por nombre o SKU..."
                value={productSearch}
                onChange={(e) => setProductSearch(e.target.value)}
              />
              {productsQuery.isLoading && (
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              )}
              {productSearch.trim().length >= 2 &&
                !productsQuery.isLoading &&
                (productsQuery.data?.items ?? []).length > 0 && (
                  <div className="space-y-1 rounded-md border p-1">
                    {(productsQuery.data?.items ?? []).map((p) => (
                      <button
                        key={p.id}
                        type="button"
                        className="flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-sm hover:bg-muted"
                        onClick={() => addItem(p)}
                      >
                        <span>
                          {p.name}{" "}
                          <span className="text-xs text-muted-foreground">
                            {p.sku}
                          </span>
                        </span>
                        <Plus className="h-4 w-4 text-muted-foreground" />
                      </button>
                    ))}
                  </div>
                )}
            </div>

            {items.length > 0 && (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Producto</TableHead>
                    <TableHead className="w-28">Cantidad</TableHead>
                    <TableHead className="w-32">Costo unit.</TableHead>
                    <TableHead className="w-32 text-right">Subtotal</TableHead>
                    <TableHead className="w-12" />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((i) => (
                    <TableRow key={i.product_id}>
                      <TableCell>
                        <p className="font-medium">{i.product_name}</p>
                        <p className="text-xs text-muted-foreground">{i.product_sku}</p>
                      </TableCell>
                      <TableCell>
                        <Input
                          type="number"
                          step="0.001"
                          value={i.quantity}
                          onChange={(e) =>
                            setItems((prev) =>
                              prev.map((x) =>
                                x.product_id === i.product_id
                                  ? { ...x, quantity: e.target.value }
                                  : x
                              )
                            )
                          }
                        />
                      </TableCell>
                      <TableCell>
                        <Input
                          type="number"
                          step="0.01"
                          value={i.unit_cost}
                          onChange={(e) =>
                            setItems((prev) =>
                              prev.map((x) =>
                                x.product_id === i.product_id
                                  ? { ...x, unit_cost: e.target.value }
                                  : x
                              )
                            )
                          }
                        />
                      </TableCell>
                      <TableCell className="text-right">
                        {(Number(i.quantity) || 0) * (Number(i.unit_cost) || 0)}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() =>
                            setItems((prev) =>
                              prev.filter((x) => x.product_id !== i.product_id)
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

            <div className="flex justify-end border-t pt-4">
              <p className="text-lg font-semibold">
                Total: {total.toFixed(2)} {currency}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </RequireSection>
  );
}