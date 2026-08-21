"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { fetchKardex } from "@/lib/inventory-api";
import { isForbidden, getErrorMessage } from "@/lib/api";
import { RequireSection } from "@/components/guards";

const MOVEMENT_LABELS: Record<string, string> = {
  PURCHASE: "Compra",
  SALE: "Venta",
  RESERVATION: "Reserva",
  RELEASE_RESERVATION: "Liberación de reserva",
  PARTIAL_PAYMENT_HOLD: "Apartado",
  CREDIT_DELIVERY: "Entrega a crédito",
  SALE_COMPLETED: "Venta completada",
  RETURN: "Devolución",
  ADJUSTMENT_IN: "Ajuste (+)",
  ADJUSTMENT_OUT: "Ajuste (-)",
  REPAIR_USAGE: "Reparación",
  REPAIR_RETURN: "Retorno de reparación",
  DAMAGED: "Dañado",
  TRANSFER: "Transferencia",
};

export default function KardexPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const productId = params.id;

  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [movementType, setMovementType] = useState("");
  const [forbidden, setForbidden] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const kardexQuery = useQuery({
    queryKey: ["kardex", productId, dateFrom, dateTo, movementType],
    queryFn: () =>
      fetchKardex(productId, {
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        movement_type: movementType || undefined,
        per_page: 100,
      }),
  });

  useEffect(() => {
    if (isForbidden(kardexQuery.error)) setForbidden(true);
    else if (kardexQuery.error)
      setError(getErrorMessage(kardexQuery.error));
  }, [kardexQuery.error]);

  if (forbidden) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-destructive">
          No tienes permisos para ver el kardex.
        </CardContent>
      </Card>
    );
  }

  return (
    <RequireSection section="inventario">
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={() => router.back()}>
            <ArrowLeft className="mr-2 h-4 w-4" /> Volver
          </Button>
          <div>
            <h1 className="text-2xl font-semibold">
              {kardexQuery.data?.product_name ?? "Kardex"}
            </h1>
            <p className="text-sm text-muted-foreground">
              {kardexQuery.data?.sku} · Saldo final:{" "}
              {kardexQuery.data?.final_balance ?? "—"}
            </p>
          </div>
        </div>

        {error && (
          <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}

        <div className="flex flex-wrap items-center gap-3">
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Desde</label>
            <Input
              type="datetime-local"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Hasta</label>
            <Input
              type="datetime-local"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Tipo</label>
            <Select
              value={movementType}
              onChange={(e) => setMovementType(e.target.value)}
            >
              <option value="">Todos</option>
              {Object.entries(MOVEMENT_LABELS).map(([key, label]) => (
                <option key={key} value={key}>
                  {label}
                </option>
              ))}
            </Select>
          </div>
        </div>

        <Card>
          <CardContent className="p-0">
            {kardexQuery.isLoading ? (
              <div className="flex justify-center py-10">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Fecha</TableHead>
                    <TableHead>Tipo</TableHead>
                    <TableHead className="text-right">Cantidad</TableHead>
                    <TableHead className="text-right">Costo unit.</TableHead>
                    <TableHead className="text-right">Saldo</TableHead>
                    <TableHead>Documento</TableHead>
                    <TableHead>Notas</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(kardexQuery.data?.items ?? []).map((m) => (
                    <TableRow key={m.id}>
                      <TableCell className="whitespace-nowrap text-xs">
                        {new Date(m.created_at).toLocaleString("es-PE")}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            Number(m.quantity) >= 0
                              ? "secondary"
                              : "destructive"
                          }
                        >
                          {MOVEMENT_LABELS[m.movement_type] ?? m.movement_type}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">{m.quantity}</TableCell>
                      <TableCell className="text-right">{m.unit_cost ?? "—"}</TableCell>
                      <TableCell className="text-right font-medium">
                        {m.balance}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {m.reference_type ?? "—"}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground max-w-[200px] truncate">
                        {m.notes ?? ""}
                      </TableCell>
                    </TableRow>
                  ))}
                  {(kardexQuery.data?.items ?? []).length === 0 && (
                    <TableRow>
                      <TableCell
                        colSpan={7}
                        className="py-10 text-center text-sm text-muted-foreground"
                      >
                        Sin movimientos para los filtros seleccionados.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </RequireSection>
  );
}