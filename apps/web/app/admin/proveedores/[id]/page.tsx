"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  fetchPurchases,
  fetchSupplier,
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

export default function ProveedorDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { user } = useAuth();
  const isOwner = user?.is_superuser ?? false;
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);

  const supplierQuery = useQuery({
    queryKey: ["supplier", params.id],
    queryFn: () => fetchSupplier(params.id),
  });

  const purchasesQuery = useQuery({
    queryKey: ["purchases", params.id],
    queryFn: () =>
      fetchPurchases({ supplier_id: params.id, per_page: 20 }),
  });

  useEffect(() => {
    const err = supplierQuery.error ?? purchasesQuery.error;
    if (isForbidden(err)) setForbidden(true);
    else if (err) setError(getErrorMessage(err));
  }, [supplierQuery.error, purchasesQuery.error]);

  const s = supplierQuery.data;

  if (forbidden) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-destructive">
          No tienes permisos para ver proveedores.
        </CardContent>
      </Card>
    );
  }

  return (
    <RequireSection section="proveedores">
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={() => router.back()}>
            <ArrowLeft className="mr-2 h-4 w-4" /> Volver
          </Button>
          <div className="flex-1">
            <h1 className="text-2xl font-semibold">
              {s?.razon_social ?? "Proveedor"}
            </h1>
            <p className="text-sm text-muted-foreground">
              {s?.ruc ?? "Sin RUC"} · {s?.ciudad ?? "—"}
            </p>
          </div>
          {isOwner && (
            <Button asChild variant="outline">
              <Link href={`/admin/proveedores/${params.id}/editar`}>Editar</Link>
            </Button>
          )}
        </div>

        {error && (
          <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}

        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Datos de contacto</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p>
                <span className="text-muted-foreground">Contacto:</span>{" "}
                {s?.contacto_nombre ?? "—"}
              </p>
              <p>
                <span className="text-muted-foreground">Teléfono:</span>{" "}
                {s?.telefono ?? "—"}
              </p>
              <p>
                <span className="text-muted-foreground">WhatsApp:</span>{" "}
                {s?.telefono_whatsapp ?? "—"}
              </p>
              <p>
                <span className="text-muted-foreground">Email:</span> {s?.email ?? "—"}
              </p>
              <p>
                <span className="text-muted-foreground">Dirección:</span>{" "}
                {s?.direccion ?? "—"}
              </p>
              <p>
                <span className="text-muted-foreground">Notas:</span>{" "}
                {s?.notes ?? "—"}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Historial de compras</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Código</TableHead>
                    <TableHead className="text-right">Total</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead>Fecha</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(purchasesQuery.data?.items ?? []).map((p) => (
                    <TableRow key={p.id}>
                      <TableCell>
                        <Link
                          href={`/admin/compras/${p.id}`}
                          className="text-sm font-medium underline-offset-4 hover:underline"
                        >
                          {p.code}
                        </Link>
                      </TableCell>
                      <TableCell className="text-right">
                        {p.total} {p.currency}
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">
                          {STATUS_LABELS[p.status] ?? p.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="whitespace-nowrap text-xs">
                        {new Date(p.created_at).toLocaleDateString("es-PE")}
                      </TableCell>
                    </TableRow>
                  ))}
                  {purchasesQuery.isLoading && (
                    <TableRow>
                      <TableCell colSpan={4} className="py-6 text-center">
                        <Loader2 className="mx-auto h-5 w-5 animate-spin text-muted-foreground" />
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      </div>
    </RequireSection>
  );
}