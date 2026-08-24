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
  QUOTE_STATUS_BADGE,
  QUOTE_STATUS_LABELS,
  fetchQuotes,
} from "@/lib/quotes-api";
import { getErrorMessage, isForbidden } from "@/lib/api";
import { RequireSection } from "@/components/guards";

export default function CotizacionesPage() {
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

  const quotesQuery = useQuery({
    queryKey: ["quotes", status, debounced, page],
    queryFn: () =>
      fetchQuotes({
        status: status || undefined,
        search: debounced || undefined,
        page,
        per_page: 15,
      }),
  });

  useEffect(() => {
    if (isForbidden(quotesQuery.error)) setForbidden(true);
    else if (quotesQuery.error) setError(getErrorMessage(quotesQuery.error));
  }, [quotesQuery.error]);

  if (forbidden) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-destructive">
          No tienes permisos para ver cotizaciones.
        </CardContent>
      </Card>
    );
  }

  const totalPages = Math.max(
    1,
    Math.ceil((quotesQuery.data?.total ?? 0) / 15)
  );

  return (
    <RequireSection section="cotizaciones">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Cotizaciones</h1>
            <p className="text-sm text-muted-foreground">
              {quotesQuery.data?.total ?? 0} cotizaciones
            </p>
          </div>
          <Button asChild>
            <Link href="/admin/cotizaciones/nuevo">
              <Plus className="mr-2 h-4 w-4" /> Nueva cotización
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
            {Object.entries(QUOTE_STATUS_LABELS).map(([key, label]) => (
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
            {quotesQuery.isLoading ? (
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
                    <TableHead>Estado</TableHead>
                    <TableHead>Vence</TableHead>
                    <TableHead>WhatsApp</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(quotesQuery.data?.items ?? []).map((q) => (
                    <TableRow key={q.id}>
                      <TableCell className="font-medium">{q.code}</TableCell>
                      <TableCell>{q.customer_name ?? "—"}</TableCell>
                      <TableCell className="text-right">
                        S/ {q.total}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={QUOTE_STATUS_BADGE[q.status] ?? "secondary"}
                        >
                          {QUOTE_STATUS_LABELS[q.status] ?? q.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="whitespace-nowrap text-xs">
                        {new Date(q.valid_until).toLocaleDateString("es-PE")}
                      </TableCell>
                      <TableCell className="text-xs">
                        {q.sent_via_whatsapp ? "Enviado" : "—"}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="sm" asChild>
                          <Link href={`/admin/cotizaciones/${q.id}`}>Ver</Link>
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
