"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Plus } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/use-auth";
import { createBrand, fetchBrands } from "@/lib/catalog-api";
import { getErrorMessage } from "@/lib/api";

export default function MarcasPage() {
  const { user } = useAuth();
  const isOwner = user?.is_superuser === true;
  const queryClient = useQueryClient();

  const brandsQuery = useQuery({ queryKey: ["brands"], queryFn: fetchBrands });

  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: () => createBrand({ name }),
    onSuccess: () => {
      setOpen(false);
      setName("");
      void queryClient.invalidateQueries({ queryKey: ["brands"] });
    },
    onError: (e) => setError(getErrorMessage(e)),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Marcas</h1>
          <p className="text-sm text-muted-foreground">
            {(brandsQuery.data ?? []).length} marcas
          </p>
        </div>
        {isOwner && (
          <Button onClick={() => setOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Nueva marca
          </Button>
        )}
      </div>

      {error && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      <Card>
        <CardContent className="p-0">
          {brandsQuery.isLoading ? (
            <div className="flex justify-center py-10">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-4 p-6 sm:grid-cols-3 lg:grid-cols-4">
              {(brandsQuery.data ?? []).map((brand) => (
                <div
                  key={brand.id}
                  className="flex items-center justify-between rounded-md border p-3"
                >
                  <span className="font-medium">{brand.name}</span>
                  <Badge variant={brand.active ? "success" : "secondary"}>
                    {brand.active ? "Activa" : "Inactiva"}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nueva marca</DialogTitle>
            <DialogDescription>
              Ej: HP, Lenovo, Samsung, Canon...
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="brandName">Nombre</Label>
              <Input
                id="brandName"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            <Button
              className="w-full"
              disabled={!name || createMutation.isPending}
              onClick={() => createMutation.mutate()}
            >
              Crear marca
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}