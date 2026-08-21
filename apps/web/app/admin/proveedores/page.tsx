"use client";

import { useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Plus, Search } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { deactivateSupplier, fetchSuppliers } from "@/lib/inventory-api";
import { getErrorMessage, isForbidden } from "@/lib/api";
import { useAuth } from "@/hooks/use-auth";
import { RequireSection } from "@/components/guards";

export default function ProveedoresPage() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const isOwner = user?.is_superuser ?? false;

  const [search, setSearch] = useState("");
  const [debounced, setDebounced] = useState("");
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);

  const suppliersQuery = useQuery({
    queryKey: ["suppliers", debounced, page],
    queryFn: () =>
      fetchSuppliers({ search: debounced || undefined, page, per_page: 15 }),
  });

  const invalidate = () =>
    void queryClient.invalidateQueries({ queryKey: ["suppliers"] });

  const deactivateMutation = useMutation({
    mutationFn: deactivateSupplier,
    onSuccess: invalidate,
    onError: (e) => {
      if (isForbidden(e)) setForbidden(true);
      setError(getErrorMessage(e));
    },
  });

  if (forbidden) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-destructive">
          No tienes permisos para gestionar proveedores.
        </CardContent>
      </Card>
    );
  }

  const totalPages = Math.max(
    1,
    Math.ceil((suppliersQuery.data?.total ?? 0) / 15)
  );

  return (
    <RequireSection section="proveedores">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Proveedores</h1>
            <p className="text-sm text-muted-foreground">
              {suppliersQuery.data?.total ?? 0} proveedores
            </p>
          </div>
          {isOwner && (
            <Button asChild>
              <Link href="/admin/proveedores/nuevo">
                <Plus className="mr-2 h-4 w-4" /> Nuevo proveedor
              </Link>
            </Button>
          )}
        </div>

        {error && (
          <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}

        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Buscar por razón social, RUC o contacto..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              window.setTimeout(() => setDebounced(e.target.value), 300);
            }}
          />
        </div>

        <Card>
          <CardContent className="p-0">
            {suppliersQuery.isLoading ? (
              <div className="flex justify-center py-10">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Razón social</TableHead>
                    <TableHead>RUC</TableHead>
                    <TableHead>Contacto</TableHead>
                    <TableHead>Teléfono</TableHead>
                    <TableHead>Ciudad</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(suppliersQuery.data?.items ?? []).map((s) => (
                    <TableRow key={s.id}>
                      <TableCell className="font-medium">{s.razon_social}</TableCell>
                      <TableCell>{s.ruc ?? "—"}</TableCell>
                      <TableCell>{s.contacto_nombre ?? "—"}</TableCell>
                      <TableCell>{s.telefono ?? "—"}</TableCell>
                      <TableCell>{s.ciudad ?? "—"}</TableCell>
                      <TableCell>
                        <Badge variant={s.active ? "success" : "destructive"}>
                          {s.active ? "Activo" : "Inactivo"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button variant="ghost" size="sm" asChild>
                            <Link href={`/admin/proveedores/${s.id}`}>Ver</Link>
                          </Button>
                          {isOwner && s.active && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => deactivateMutation.mutate(s.id)}
                            >
                              Desactivar
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
      </div>
    </RequireSection>
  );
}