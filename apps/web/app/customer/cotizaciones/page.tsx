"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { QUOTE_STATUS_BADGE, QUOTE_STATUS_LABELS } from "@/lib/quotes-api";
import { api } from "@/lib/api";
import type { QuoteSummary } from "@/lib/types";
import { getErrorMessage } from "@/lib/api";

async function fetchMyQuotes(): Promise<QuoteSummary[]> {
  const { data } = await api.get<QuoteSummary[]>("/quotes/my");
  return data;
}

export default function MisCotizacionesPage() {
  const quotesQuery = useQuery({
    queryKey: ["my-quotes"],
    queryFn: fetchMyQuotes,
  });

  if (quotesQuery.isLoading) {
    return (
      <div className="flex justify-center py-10">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (quotesQuery.error) {
    return (
      <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
        {getErrorMessage(quotesQuery.error)}
      </p>
    );
  }

  const quotes = quotesQuery.data ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Mis cotizaciones</h1>
        <p className="text-sm text-muted-foreground">
          {quotes.length} cotización(es) a tu nombre
        </p>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Código</TableHead>
                <TableHead className="text-right">Total</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead>Válida hasta</TableHead>
                <TableHead className="text-right">Ver detalle</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {quotes.map((q) => (
                <TableRow key={q.id}>
                  <TableCell className="font-medium">{q.code}</TableCell>
                  <TableCell className="text-right">S/ {q.total}</TableCell>
                  <TableCell>
                    <Badge variant={QUOTE_STATUS_BADGE[q.status] ?? "secondary"}>
                      {QUOTE_STATUS_LABELS[q.status] ?? q.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs">
                    {new Date(q.valid_until).toLocaleDateString("es-PE")}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="sm" asChild>
                      <Link href={`/cotizacion/${q.code}`}>Abrir link</Link>
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
