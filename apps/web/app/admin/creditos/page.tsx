"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Loader2, Plus } from "lucide-react";
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
import {
  AGREEMENT_STATUS_BADGE,
  AGREEMENT_STATUS_LABELS,
  fetchCredits,
} from "@/lib/credits-api";
import { getErrorMessage, isForbidden } from "@/lib/api";
import { RequireSection } from "@/components/guards";

export default function CreditosPage() {
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const [debounced, setDebounced] = useState("");
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);

  useEffect(() => {
    const t = window.setTimeout(() => setDebounced(search), 300);
    return () => window.clearTimeout(t);
  }, [search]);

  const creditsQuery = useQuery({
    queryKey: ["credits", status, debounced, page],
    queryFn: () =>
      fetchCredits({
        status: status || undefined,
        search: debounced || undefined,
        page,
        per_page: 15,
      }),
  });

  useEffect(() => {
    if (isForbidden(creditsQuery.error)) setForbidden(true);
    else if (creditsQuery.error)
      setError(getErrorMessage(creditsQuery.error));
  }, [creditsQuery.error]);

  if (forbidden) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-destructive">
          No tienes permisos para ver créditos.
        </CardContent>
      </Card>
    );
  }

  const totalPages = Math.max(
    1,
    Math.ceil((creditsQuery.data?.total ?? 0) / 15)
  );

  return (
    <RequireSection section="creditos">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Créditos</h1>
            <p className="text-sm text-muted-foreground">
              {creditsQuery.data?.total ?? 0} acuerdos
            </p>
          </div>
          <Button asChild>
            <Link href="/admin/creditos/nuevo">
              <Plus className="mr-2 h-4 w-4" /> Nuevo crédito
            </Link>
          </Button>
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
            {Object.entries(AGREEMENT_STATUS_LABELS).map(([key, label]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </Select>
          <Input
            placeholder="Buscar por código o cliente…"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-64"
          />
        </div>

        <Card>
          <CardContent className="p-0">
            {creditsQuery.isLoading ? (
              <div className="flex justify-center py-10">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Código</TableHead>
                    <TableHead>Cliente</TableHead>
                    <TableHead className="text-right">Total</TableHead>
                    <TableHead className="text-right">Cuotas</TableHead>
                    <TableHead className="text-right">Pendiente</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead>Fecha</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(creditsQuery.data?.items ?? []).map((c) => (
                    <TableRow key={c.id}>
                      <TableCell className="font-medium">{c.code}</TableCell>
                      <TableCell>{c.customer_name ?? "—"}</TableCell>
                      <TableCell className="text-right">
                        {c.total_amount}
                      </TableCell>
                      <TableCell className="text-right">
                        {c.paid_installments}/{c.number_of_installments}
                        {c.overdue_installments > 0 && (
                          <span className="ml-1 text-xs text-destructive">
                            ({c.overdue_installments} venc.)
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        {c.pending_total}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            AGREEMENT_STATUS_BADGE[c.status] ?? "secondary"
                          }
                        >
                          {AGREEMENT_STATUS_LABELS[c.status] ?? c.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="whitespace-nowrap text-xs">
                        {new Date(c.created_at).toLocaleDateString("es-PE")}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="sm" asChild>
                          <Link href={`/admin/creditos/${c.id}`}>Ver</Link>
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
