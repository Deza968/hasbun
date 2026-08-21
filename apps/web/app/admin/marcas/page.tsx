"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Plus } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createBrand, deactivateBrand, fetchBrands } from "@/lib/catalog-api";
import { getErrorMessage, isForbidden } from "@/lib/api";
import { useAuth } from "@/hooks/use-auth";
import { RequireSection } from "@/components/guards";

export default function MarcasPage() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const isOwner = user?.is_superuser ?? false;

  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);

  const brandsQuery = useQuery({
    queryKey: ["brands"],
    queryFn: fetchBrands,
  });

  const invalidate = () => void queryClient.invalidateQueries({ queryKey: ["brands"] });

  const createMutation = useMutation({
    mutationFn: () => createBrand({ name }),
    onSuccess: () => {
      setOpen(false);
      setName("");
      invalidate();
    },
    onError: (e) => {
      if (isForbidden(e)) setForbidden(true);
      setError(getErrorMessage(e));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deactivateBrand,
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
          No tienes permisos para gestionar marcas.
        </CardContent>
      </Card>
    );
  }

  return (
    <RequireSection section="marcas">
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Marcas</h1>
          <p className="text-sm text-muted-foreground">
            {brandsQuery.data?.length ?? 0} marcas registradas
          </p>
        </div>
        {isOwner && (
          <Button onClick={() => setOpen(true)}>
            <Plus className="mr-2 h-4 w-4" /> Nueva
          </Button>
        )}
      </div>

      {error && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>
      )}

      <Card>
        <CardContent className="py-4">
          <div className="grid gap-2">
            {(brandsQuery.data ?? []).map((brand) => (
              <div
                key={brand.id}
                className="flex items-center justify-between rounded border p-3 text-sm"
              >
                <div className="flex items-center gap-2">
                  <span>{brand.name}</span>
                  <Badge variant="secondary" className="lowercase">
                    {brand.slug}
                  </Badge>
                  {!brand.active && <Badge variant="destructive">inactiva</Badge>}
                </div>
                {isOwner && brand.active && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => deleteMutation.mutate(brand.id)}
                  >
                    Desactivar
                  </Button>
                )}
              </div>
            ))}
            {(brandsQuery.data ?? []).length === 0 && (
              <p className="text-sm text-muted-foreground">Sin marcas registradas.</p>
            )}
          </div>
        </CardContent>
      </Card>

      {open && (
        <Card>
          <CardHeader>
            <CardTitle>Nueva marca</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Nombre</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div className="flex gap-2">
              <Button
                disabled={!name || createMutation.isPending}
                onClick={() => createMutation.mutate()}
              >
                {createMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Crear
              </Button>
              <Button variant="ghost" onClick={() => setOpen(false)}>
                Cancelar
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
    </RequireSection>
  );
}