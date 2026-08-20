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
import { Select } from "@/components/ui/select";
import { useAuth } from "@/hooks/use-auth";
import {
  addAttributeValue,
  createAttribute,
  fetchAttributes,
} from "@/lib/catalog-api";
import { getErrorMessage } from "@/lib/api";

export default function AtributosPage() {
  const { user } = useAuth();
  const isOwner = user?.is_superuser === true;
  const queryClient = useQueryClient();

  const attributesQuery = useQuery({
    queryKey: ["attributes"],
    queryFn: fetchAttributes,
  });

  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [dataType, setDataType] = useState("text");
  const [unit, setUnit] = useState("");
  const [error, setError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: () =>
      createAttribute({ name, data_type: dataType, unit: unit || null }),
    onSuccess: () => {
      setOpen(false);
      setName("");
      setUnit("");
      void queryClient.invalidateQueries({ queryKey: ["attributes"] });
    },
    onError: (e) => setError(getErrorMessage(e)),
  });

  const valueMutation = useMutation({
    mutationFn: ({ attributeId, value }: { attributeId: string; value: string }) =>
      addAttributeValue(attributeId, value),
    onSuccess: () =>
      void queryClient.invalidateQueries({ queryKey: ["attributes"] }),
    onError: (e) => setError(getErrorMessage(e)),
  });

  const [valueInputs, setValueInputs] = useState<Record<string, string>>({});

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Atributos</h1>
          <p className="text-sm text-muted-foreground">
            Sistema de atributos dinámicos del catálogo
          </p>
        </div>
        {isOwner && (
          <Button onClick={() => setOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Nuevo atributo
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
          {attributesQuery.isLoading ? (
            <div className="flex justify-center py-10">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <div className="divide-y">
              {(attributesQuery.data ?? []).map((attribute) => (
                <div key={attribute.id} className="p-4">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{attribute.name}</span>
                    <Badge variant="secondary">{attribute.data_type}</Badge>
                    {attribute.unit && (
                      <span className="text-xs text-muted-foreground">
                        {attribute.unit}
                      </span>
                    )}
                  </div>
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    {attribute.values.map((value) => (
                      <Badge key={value.id} variant="outline">
                        {value.value}
                      </Badge>
                    ))}
                    <div className="flex items-center gap-2">
                      <Input
                        className="h-8 w-36"
                        placeholder="+ valor"
                        value={valueInputs[attribute.id] ?? ""}
                        onChange={(e) =>
                          setValueInputs((prev) => ({
                            ...prev,
                            [attribute.id]: e.target.value,
                          }))
                        }
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={!(valueInputs[attribute.id] ?? "").trim()}
                        onClick={() =>
                          valueMutation.mutate({
                            attributeId: attribute.id,
                            value: (valueInputs[attribute.id] ?? "").trim(),
                          })
                        }
                      >
                        Agregar
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nuevo atributo</DialogTitle>
            <DialogDescription>
              Ej: Color, RAM, Capacidad, Garantía...
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="attrName">Nombre</Label>
              <Input
                id="attrName"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="dataType">Tipo de dato</Label>
                <Select
                  id="dataType"
                  value={dataType}
                  onChange={(e) => setDataType(e.target.value)}
                >
                  <option value="text">Texto</option>
                  <option value="number">Número</option>
                  <option value="boolean">Booleano</option>
                  <option value="list">Lista</option>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="unit">Unidad (opcional)</Label>
                <Input
                  id="unit"
                  placeholder="GB, GHz, cm..."
                  value={unit}
                  onChange={(e) => setUnit(e.target.value)}
                />
              </div>
            </div>
            <Button
              className="w-full"
              disabled={!name || createMutation.isPending}
              onClick={() => createMutation.mutate()}
            >
              Crear atributo
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}