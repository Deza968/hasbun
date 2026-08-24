"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { Check, Loader2, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { QUOTE_STATUS_LABELS } from "@/lib/quotes-api";
import { API_URL, getErrorMessage } from "@/lib/api";

interface PublicQuote {
  code: string;
  status: string;
  customer_name: string | null;
  total: string;
  currency: string;
  valid_until: string;
  notes: string | null;
  items: {
    product_name: string | null;
    quantity: string;
    unit_price: string;
    subtotal: string;
  }[];
}

async function fetchPublicQuote(code: string): Promise<PublicQuote> {
  const { data } = await axios.get<PublicQuote>(
    `${API_URL}/quotes/${code}/public`
  );
  return data;
}

async function respondPublicQuote(
  code: string,
  decision: "accept" | "reject",
  reason?: string
): Promise<PublicQuote> {
  const { data } = await axios.post<PublicQuote>(
    `${API_URL}/quotes/${code}/public/respond`,
    { decision, reason }
  );
  return data;
}

export default function CotizacionPublicaPage({
  params,
}: {
  params: Promise<{ code: string }>;
}) {
  const { code } = use(params);
  const [rejecting, setRejecting] = useState(false);
  const [reason, setReason] = useState("");
  const queryClient = useQueryClient();

  const quoteQuery = useQuery({
    queryKey: ["public-quote", code],
    queryFn: () => fetchPublicQuote(code),
  });

  const respond = useMutation({
    mutationFn: (decision: "accept" | "reject") =>
      respondPublicQuote(code, decision, reason || undefined),
    onSuccess: () =>
      void queryClient.invalidateQueries({
        queryKey: ["public-quote", code],
      }),
  });

  if (quoteQuery.isLoading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (quoteQuery.error) {
    return (
      <div className="mx-auto max-w-lg py-16 text-center">
        <h1 className="text-xl font-semibold">Cotización no encontrada</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Verifica el enlace o contacta a la tienda.
        </p>
      </div>
    );
  }

  const quote = quoteQuery.data;
  const canRespond = quote?.status === "SENT" || quote?.status === "VIEWED";
  const responded =
    quote?.status === "ACCEPTED" ||
    quote?.status === "REJECTED";

  return (
    <div className="mx-auto max-w-2xl space-y-6 py-10">
      <div className="text-center">
        <p className="text-sm text-muted-foreground">Inversiones Hasbun</p>
        <h1 className="text-2xl font-semibold">Cotización {quote?.code}</h1>
        {quote && (
          <Badge variant="outline" className="mt-2">
            {QUOTE_STATUS_LABELS[quote.status] ?? quote.status}
          </Badge>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Detalle</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Producto</TableHead>
                <TableHead className="text-right">Cantidad</TableHead>
                <TableHead className="text-right">Precio</TableHead>
                <TableHead className="text-right">Subtotal</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(quote?.items ?? []).map((item, i) => (
                <TableRow key={i}>
                  <TableCell>{item.product_name ?? "—"}</TableCell>
                  <TableCell className="text-right">{item.quantity}</TableCell>
                  <TableCell className="text-right">
                    S/ {item.unit_price}
                  </TableCell>
                  <TableCell className="text-right">
                    S/ {item.subtotal}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          <div className="flex items-center justify-between border-t pt-4">
            <p className="text-sm text-muted-foreground">
              Válida hasta{" "}
              {quote && new Date(quote.valid_until).toLocaleDateString("es-PE")}
            </p>
            <p className="text-xl font-semibold">Total: S/ {quote?.total}</p>
          </div>

          {quote?.notes && (
            <p className="whitespace-pre-line rounded-md bg-muted px-3 py-2 text-sm">
              {quote.notes}
            </p>
          )}
        </CardContent>
      </Card>

      {canRespond && !respond.isPending && (
        <Card>
          <CardContent className="space-y-4 pt-6">
            <p className="text-center text-sm text-muted-foreground">
              ¿Aceptas esta cotización? Tu respuesta se registra al instante.
            </p>

            {rejecting ? (
              <div className="space-y-3">
                <textarea
                  aria-label="Motivo del rechazo"
                  className="w-full rounded-md border px-3 py-2 text-sm"
                  rows={3}
                  placeholder="Motivo del rechazo (opcional)"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                />
                <div className="flex justify-center gap-3">
                  <Button
                    variant="outline"
                    onClick={() => setRejecting(false)}
                  >
                    Volver
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={() => respond.mutate("reject")}
                  >
                    Confirmar rechazo
                  </Button>
                </div>
              </div>
            ) : (
              <div className="flex justify-center gap-3">
                <Button onClick={() => respond.mutate("accept")}>
                  <Check className="mr-2 h-4 w-4" /> Aceptar cotización
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => setRejecting(true)}
                >
                  <X className="mr-2 h-4 w-4" /> Rechazar
                </Button>
              </div>
            )}

            {respond.error && (
              <p className="text-center text-sm text-destructive">
                {getErrorMessage(respond.error)}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {responded && (
        <p className="text-center text-sm text-muted-foreground">
          Gracias por tu respuesta. Contáctanos para coordinar tu compra.
        </p>
      )}

      <p className="text-center text-xs text-muted-foreground">
        <Link href="/" className="underline">
          Ir a la tienda
        </Link>
      </p>
    </div>
  );
}
