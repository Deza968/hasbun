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
import { Select } from "@/components/ui/select";
import {
  addAttributeValue,
  createAttribute,
  fetchAttributes,
  fetchAttributeValues,
} from "@/lib/catalog-api";
import { getErrorMessage, isForbidden } from "@/lib/api";
import { useAuth } from "@/hooks/use-auth";

const DATA_TYPES = [
  { value: "STRING", label: "Texto" },
  { value: "INTEGER", label: "Número entero" },
  { value: "DECIMAL", label: "Decimal" },
  { value: "BOOLEAN", label: "Sí/No" },
];

export default function AtributosPage() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const isOwner = user?.is_superuser ?? false;

  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [dataType, setDataType] = useState("STRING");
  const [unit, setUnit] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);

  const [valuesFor, setValuesFor] = useState<string | null>(null);
  const [newValue, setNewValue] = useState("");

  const attributesQuery = useQuery({
    queryKey: ["attributes"],
    queryFn: fetchAttributes,
  });

  const valuesQuery = useQuery({
    queryKey: ["attribute-values", valuesFor],
    queryFn: () => fetchAttributeValues(valuesFor as string),
    enabled: !!valuesFor,
  });

  const invalidateAttributes = () =>
    void queryClient.invalidateQueries({ queryKey: ["attributes"] });

  const createMutation = useMutation({
    mutationFn: () => createAttribute({ name, data_type: dataType, unit: unit || null }),
    onSuccess: () => {
      setOpen(false);
      setName("");
      setUnit("");
      invalidateAttributes();
    },
    onError: (e) => {
      if (isForbidden(e)) setForbidden(true);
      setError(getErrorMessage(e));
    },
  });

  const valueMutation = useMutation({
    mutationFn: () => addAttributeValue(valuesFor as string, newValue),
    onSuccess: () => {
      setNewValue("");
      void queryClient.invalidateQueries({
        queryKey: ["attribute-values", valuesFor],
      });
    },
    onError: (e) => {
      if (isForbidden(e)) setForbidden(true);
      setError(getErrorMessage(e));
    },
  });

  if (forbidden) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-destructive">
          No tienes permisos para gestionar atributos.
        </CardContent>
      </Card>
    );
  }

  const activeAttr = valuesFor
    ? (attributesQuery.data ?? []).find((a) => a.id === valuesFor)
    : null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Atributos</h1>
          <p className="text-sm text-muted-foreground">
            Características dinámicas de los productos
          </p>
        </div>
        {isOwner && (
          <Button onClick={() => setOpen(true)}>
            <Plus className="mr-2 h-4 w-4" /> Nuevo
          </Button>
        )}
      </div>

      {error && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>
      )}

      <Card>
        <CardContent className="py-4">
          <div className="grid gap-2">
            {(attributesQuery.data ?? []).map((attr) => (
              <div
                key={attr.id}
                className="flex items-center justify-between rounded border p-3 text-sm"
              >
                <div className="flex items-center gap-2">
                  <span>{attr.name}</span>
                  <Badge variant="secondary">{attr.data_type}</Badge>
                  {attr.unit && <Badge variant="outline">{attr.unit}</Badge>}
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setValuesFor(valuesFor === attr.id ? null : attr.id);
                    setNewValue("");
                  }}
                >
                  Valores
                </Button>
              </div>
            ))}
            {(attributesQuery.data ?? []).length === 0 && (
              <p className="text-sm text-muted-foreground">Sin atributos.</p>
            )}
          </div>
        </CardContent>
      </Card>

      {activeAttr && (
        <Card>
          <CardHeader>
            <CardTitle>Valores de «{activeAttr.name}»</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex flex-wrap gap-2">
              {(valuesQuery.data ?? []).map((v) => (
                <Badge key={v.id} variant="secondary">
                  {v.value}
                </Badge>
              ))}
              {(valuesQuery.data ?? []).length === 0 && (
                <p className="text-sm text-muted-foreground">Sin valores predefinidos.</p>
              )}
            </div>
            {isOwner && (
              <div className="flex items-end gap-2">
                <div className="flex-1 space-y-1">
                  <Label>Nuevo valor</Label>
                  <Input
                    value={newValue}
                    onChange={(e) => setNewValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && newValue) valueMutation.mutate();
                    }}
                  />
                </div>
                <Button
                  disabled={!newValue || valueMutation.isPending}
                  onClick={() => valueMutation.mutate()}
                >
                  {valueMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Agregar
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {open && (
        <Card>
          <CardHeader>
            <CardTitle>Nuevo atributo</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Nombre</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label>Tipo de dato</Label>
                <Select value={dataType} onChange={(e) => setDataType(e.target.value)}>
                  {DATA_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Unidad (opcional)</Label>
                <Input value={unit} onChange={(e) => setUnit(e.target.value)} />
              </div>
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
  );
}