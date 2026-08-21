"use client";

import { useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, PackageSearch, Search } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
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
import { createAdjustment, fetchStock } from "@/lib/inventory-api";
import { getErrorMessage, isForbidden } from "@/lib/api";
import { useAuth } from "@/hooks/use-auth";
import { RequireSection } from "@/components/guards";
import { Download } from "lucide-react";

export default function InventarioPage() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const isOwner = user?.is_superuser ?? false;

  const [search, setSearch] = useState("");
  const [debounced, setDebounced] = useState("");
  const [low, setLow] = useState("");
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);

  const [adjust, setAdjust] = useState<{
    product_id: string;
    product_name: string;
  } | null>(null);
  const [qty, setQty] = useState("");
  const [reason, setReason] = useState("");

  const stockQuery = useQuery({
    queryKey: ["stock", debounced, low, page],
    queryFn: () =>
      fetchStock({
        search: debounced || undefined,
        low: low === "" ? undefined : low === "low",
        page,
        per_page: 15,
      }),
  });

  const invalidate = () => void queryClient.invalidateQueries({ queryKey: ["stock"] });

  const adjustMutation = useMutation({
    mutationFn: () =>
      createAdjustment({
        product_id: adjust!.product_id,
        quantity: qty,
        reason,
      }),
    onSuccess: () => {
      setAdjust(null);
      setQty("");
      setReason("");
      invalidate();
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
          No tienes permisos para ver el inventario.
        </CardContent>
      </Card>
    );
  }

  const totalPages = Math.max(
    1,
    Math.ceil((stockQuery.data?.total ?? 0) / 15)
  );

  const stockBadge = (s: { available: string; stock_minimum: number }) => {
    const available = Number(s.available);
    if (available <= 0) return <Badge variant="destructive">Agotado</Badge>;
    if (available <= s.stock_minimum)
      return <Badge variant="secondary">Stock bajo</Badge>;
    return <Badge variant="success">OK</Badge>;
  };

  return (
    <RequireSection section="inventario">
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Inventario</h1>
          <p className="text-sm text-muted-foreground">
            {stockQuery.data?.total ?? 0} productos
          </p>
        </div>

        {error && (
          <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}

        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[220px]">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="pl-9"
              placeholder="Buscar por nombre o SKU..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                window.setTimeout(
                  () => setDebounced(e.target.value),
                  300
                );
              }}
            />
          </div>
          <Select
            value={low}
            onChange={(e) => {
              setLow(e.target.value);
              setPage(1);
            }}
          >
            <option value="">Todos los estados</option>
            <option value="low">Solo stock bajo</option>
            <option value="ok">Stock OK</option>
          </Select>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              const rows = stockQuery.data?.items ?? [];
              if (rows.length === 0) return;
              const header = ["SKU", "Producto", "Disponible", "Reservado", "En crédito", "Total físico", "Stock mínimo"].join(",");
              const csv = [header, ...rows.map((r) => [r.sku, `"${r.product_name ?? ""}"`, r.available, r.reserved, r.on_credit, r.total_physical, r.stock_minimum].join(","))].join("\n");
              const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = `inventario_${new Date().toISOString().slice(0,10)}.csv`;
              a.click();
              URL.revokeObjectURL(url);
            }}
          >
            <Download className="mr-2 h-4 w-4" /> Exportar CSV
          </Button>
        </div>

        <Card>
          <CardContent className="p-0">
            {stockQuery.isLoading ? (
              <div className="flex justify-center py-10">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Producto</TableHead>
                    <TableHead className="text-right">Disponible</TableHead>
                    <TableHead className="text-right">Reservado</TableHead>
                    <TableHead className="text-right">En crédito</TableHead>
                    <TableHead className="text-right">Total físico</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(stockQuery.data?.items ?? []).map((s) => (
                    <TableRow key={s.product_id}>
                      <TableCell>
                        <p className="font-medium">{s.product_name}</p>
                        <p className="text-xs text-muted-foreground">{s.sku}</p>
                      </TableCell>
                      <TableCell className="text-right">{s.available}</TableCell>
                      <TableCell className="text-right">{s.reserved}</TableCell>
                      <TableCell className="text-right">{s.on_credit}</TableCell>
                      <TableCell className="text-right">{s.total_physical}</TableCell>
                      <TableCell>{stockBadge(s)}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button variant="ghost" size="sm" asChild>
                            <Link href={`/admin/inventario/kardex/${s.product_id}`}>
                              Kardex
                            </Link>
                          </Button>
                          {isOwner && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() =>
                                setAdjust({
                                  product_id: s.product_id,
                                  product_name: s.product_name ?? s.sku ?? "",
                                })
                              }
                            >
                              Ajustar
                            </Button>
                          )}
                        </div>
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

        <Dialog
          open={Boolean(adjust)}
          onOpenChange={(open) => {
            if (!open) {
              setAdjust(null);
              setQty("");
              setReason("");
            }
          }}
        >
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Ajuste de inventario</DialogTitle>
              <DialogDescription>
                {adjust?.product_name}. Positivo = entrada, negativo = salida.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="qty">Cantidad</Label>
                <Input
                  id="qty"
                  type="number"
                  step="0.001"
                  value={qty}
                  onChange={(e) => setQty(e.target.value)}
                  placeholder="5 o -3"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="reason">Razón (obligatoria)</Label>
                <textarea
                  id="reason"
                  className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm"
                  rows={3}
                  placeholder="Conteo físico - diferencia de 5 unidades"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                />
              </div>
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => setAdjust(null)}
              >
                Cancelar
              </Button>
              <Button
                disabled={!qty || reason.trim().length < 5 || adjustMutation.isPending}
                onClick={() => adjustMutation.mutate()}
              >
                {adjustMutation.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : null}
                Registrar ajuste
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <PackageSearch className="h-4 w-4" />
          El stock se calcula sumando los movimientos de inventario (nunca es un
          campo editable).
        </div>
      </div>
    </RequireSection>
  );
}