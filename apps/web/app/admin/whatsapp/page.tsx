"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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
  MESSAGE_STATUS_LABELS,
  WHATSAPP_EVENT_LABELS,
  fetchWhatsAppConfig,
  fetchWhatsAppMessages,
  fetchWhatsAppTemplates,
  retryWhatsAppMessage,
  updateWhatsAppConfig,
  updateWhatsAppTemplate,
} from "@/lib/whatsapp-api";
import { getErrorMessage, isForbidden } from "@/lib/api";
import { RequireSection } from "@/components/guards";

const STATUS_BADGE: Record<
  string,
  "secondary" | "success" | "destructive" | "outline"
> = {
  PENDING: "secondary",
  SENT: "success",
  DELIVERED: "success",
  FAILED: "destructive",
};

export default function WhatsappPanelPage() {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);
  const [editingBody, setEditingBody] = useState<Record<string, string>>({});

  const messagesQuery = useQuery({
    queryKey: ["wa-messages", status, page],
    queryFn: () =>
      fetchWhatsAppMessages({ status: status || undefined, page, per_page: 20 }),
  });
  const templatesQuery = useQuery({
    queryKey: ["wa-templates"],
    queryFn: fetchWhatsAppTemplates,
  });
  const configQuery = useQuery({
    queryKey: ["wa-config"],
    queryFn: fetchWhatsAppConfig,
  });

  useEffect(() => {
    if (isForbidden(messagesQuery.error)) setForbidden(true);
    else if (messagesQuery.error)
      setError(getErrorMessage(messagesQuery.error));
  }, [messagesQuery.error]);

  const onError = (e: unknown) => setError(getErrorMessage(e));

  const retryMutation = useMutation({
    mutationFn: retryWhatsAppMessage,
    onSuccess: () =>
      void queryClient.invalidateQueries({ queryKey: ["wa-messages"] }),
    onError,
  });

  const toggleConfig = useMutation({
    mutationFn: (enabled: boolean) => updateWhatsAppConfig(enabled),
    onSuccess: (cfg) => queryClient.setQueryData(["wa-config"], cfg),
    onError,
  });

  const saveTemplate = useMutation({
    mutationFn: ({ id, body }: { id: string; body: string }) =>
      updateWhatsAppTemplate(id, { body }),
    onSuccess: () =>
      void queryClient.invalidateQueries({ queryKey: ["wa-templates"] }),
    onError,
  });

  if (forbidden) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-destructive">
          No tienes permisos para gestionar WhatsApp.
        </CardContent>
      </Card>
    );
  }

  const totalPages = Math.max(
    1,
    Math.ceil((messagesQuery.data?.total ?? 0) / 20)
  );
  const config = configQuery.data;

  return (
    <RequireSection section="whatsapp">
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold">Panel de WhatsApp</h1>
            <p className="text-sm text-muted-foreground">
              Cola de mensajes con reintentos automáticos (1/5/15 min).
            </p>
          </div>
          <div className="flex items-center gap-2">
            {config && (
              <>
                <Badge
                  variant={config.enabled ? "success" : "secondary"}
                >
                  Proveedor: {config.provider}
                </Badge>
                <Button
                  variant={config.enabled ? "destructive" : "default"}
                  size="sm"
                  disabled={toggleConfig.isPending}
                  onClick={() => toggleConfig.mutate(!config.enabled)}
                >
                  {config.enabled ? "Desactivar módulo" : "Activar módulo"}
                </Button>
              </>
            )}
          </div>
        </div>

        {error && (
          <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Mensajes</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Select
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setPage(1);
              }}
              className="w-48"
            >
              <option value="">Todos los estados</option>
              {Object.entries(MESSAGE_STATUS_LABELS).map(([key, label]) => (
                <option key={key} value={key}>
                  {label}
                </option>
              ))}
            </Select>

            {messagesQuery.isLoading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Destinatario</TableHead>
                    <TableHead>Evento</TableHead>
                    <TableHead>Mensaje</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(messagesQuery.data?.items ?? []).map((m) => (
                    <TableRow key={m.id}>
                      <TableCell className="font-mono text-xs">
                        {m.recipient}
                      </TableCell>
                      <TableCell className="text-xs">
                        {WHATSAPP_EVENT_LABELS[m.event_type] ?? m.event_type}
                      </TableCell>
                      <TableCell className="max-w-xs truncate text-xs text-muted-foreground">
                        {m.rendered}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={STATUS_BADGE[m.status] ?? "secondary"}
                        >
                          {MESSAGE_STATUS_LABELS[m.status] ?? m.status}
                        </Badge>
                        {m.retry_count > 0 && m.status !== "SENT" && (
                          <span className="ml-1 text-xs text-muted-foreground">
                            ({m.retry_count} intentos)
                          </span>
                        )}
                        {m.error && m.status === "FAILED" && (
                          <p
                            className="mt-1 max-w-[200px] truncate text-xs text-destructive"
                            title={m.error}
                          >
                            {m.error}
                          </p>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        {m.status === "FAILED" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            disabled={retryMutation.isPending}
                            onClick={() => retryMutation.mutate(m.id)}
                          >
                            <RefreshCw className="mr-1 h-3 w-3" /> Reintentar
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}

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
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Plantillas</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {(templatesQuery.data ?? []).map((t) => (
              <div key={t.id} className="rounded-md border p-3">
                <div className="mb-2 flex items-center gap-2">
                  <Badge variant="outline">
                    {WHATSAPP_EVENT_LABELS[t.event_type] ?? t.event_type}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {t.name}
                  </span>
                  {!t.active && <Badge variant="secondary">Inactiva</Badge>}
                </div>
                <div className="flex gap-2">
                  <Input
                    aria-label={`Plantilla ${t.name}`}
                    value={editingBody[t.id] ?? t.body}
                    onChange={(e) =>
                      setEditingBody((prev) => ({
                        ...prev,
                        [t.id]: e.target.value,
                      }))
                    }
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={
                      saveTemplate.isPending ||
                      editingBody[t.id] === undefined ||
                      editingBody[t.id] === t.body
                    }
                    onClick={() =>
                      saveTemplate.mutate({
                        id: t.id,
                        body: editingBody[t.id],
                      })
                    }
                  >
                    Guardar
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </RequireSection>
  );
}
