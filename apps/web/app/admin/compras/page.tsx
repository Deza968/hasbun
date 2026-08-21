"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Loader2, Plus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { fetchPurchases, fetchSuppliers } from "@/lib/inventory-api";
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

export default function ComprasPage() {
  const { user } = useAuth();
  const isOwner = user?.is_superuser ?? false;

  const [status, setStatus] = useState("");
  const [supplierId, setSupplierId] = useState("");
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);

  const suppliersQuery = useQuery({
    queryKey: ["suppliers"],
    queryFn: () => fetchSuppliers({ per_page: 100 }),
  });

  const purchasesQuery = useQuery({
    queryKey: ["purchases", status, supplierId, page],
    queryFn: () =>
      fetchPurchases({
        status: status || undefined,
        supplier_id: supplierId || undefined,
        page,
        per_page: 15,
      }),
  });

  useEffect(() => {
    if (isForbidden(purchasesQuery.error)) setForbidden(true);
    else if (purchasesQuery.error)
      setError(getErrorMessage(purchasesQuery.error));
  }, [purchasesQuery.error]);

  if (forbidden) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-destructive">
          No tienes permisos para ver compras.
        </CardContent>
      </Card>
    );
  }

  const totalPages = Math.max(
    1,
    Math.ceil((purchasesQuery.data?.total ?? 0) / 15)
  );

  return (
    <RequireSection section="compras">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Compras</h1>
            <p className="text-sm text-muted-foreground">
              {purchasesQuery.data?.total ?? 0} órdenes
            </p>
          </div>
          {isOwner && (
            <Button asChild>
              <Link href="/admin/compras/nueva">
                <Plus className="mr-2 h-4 w-4" /> Nueva compra
              </Link>
            </Button>
          )}
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
            {Object.entries(STATUS_LABELS).map(([key, label]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </Select>
          <Select
            value={supplierId}
            onChange={(e) => {
              setSupplierId(e.target.value);
              setPage(1);
            }}
          >
            <option value="">Todos los proveedores</option>
            {(suppliersQuery.data?.items ?? []).map((s) => (
              <option key={s.id} value={s.id}>
                {s.razon_social}
              </option>
            ))}
          </Select>
        </div>

        <Card>
          <CardContent className="p-0">
            {purchasesQuery.isLoading ? (
              <div className="flex justify-center py-10">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Código</TableHead>
                    <TableHead>Proveedor</TableHead>
                    <TableHead className="text-right">Total</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead>Fecha</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(purchasesQuery.data?.items ?? []).map((p) => (
                    <TableRow key={p.id}>
                      <TableCell className="font-medium">{p.code}</TableCell>
                      <TableCell>{p.supplier_name ?? "—"}</TableCell>
                      <TableCell className="text-right">
                        {p.total} {p.currency}
                      </TableCell>
                      <TableCell>
                        <Badge variant={STATUS_BADGE[p.status] ?? "secondary"}>
                          {STATUS_LABELS[p.status] ?? p.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="whitespace-nowrap text-xs">
                        {new Date(p.created_at).toLocaleString("es-PE")}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="sm" asChild>
                          <Link href={`/admin/compras/${p.id}`}>Ver</Link>
                        </Button>
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
      </div>
    </RequireSection>
  );
}