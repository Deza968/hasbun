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
  createCategory,
  deactivateCategory,
  fetchCategories,
} from "@/lib/catalog-api";
import { getErrorMessage, isForbidden } from "@/lib/api";
import { useAuth } from "@/hooks/use-auth";
import { RequireSection } from "@/components/guards";

function CategoryTree({
  nodes,
  onDelete,
  canEdit,
  depth = 0,
}: {
  nodes: any[];
  onDelete: (id: string) => void;
  canEdit: boolean;
  depth?: number;
}) {
  if (nodes.length === 0) return null;
  return (
    <ul className={`space-y-1 ${depth > 0 ? "ml-4 border-l pl-3" : ""}`}>
      {nodes.map((node: any) => (
        <li key={node.id}>
          <div className="flex items-center justify-between rounded border p-2 text-sm">
            <div className="flex items-center gap-2">
              <span>{node.name}</span>
              <Badge variant="secondary" className="lowercase">
                {node.slug}
              </Badge>
              {!node.active && <Badge variant="destructive">inactiva</Badge>}
            </div>
            {canEdit && node.active && (
              <Button variant="ghost" size="sm" onClick={() => onDelete(node.id)}>
                Desactivar
              </Button>
            )}
          </div>
          <CategoryTree nodes={node.children} onDelete={onDelete} canEdit={canEdit} depth={depth + 1} />
        </li>
      ))}
    </ul>
  );
}

export default function CategoriasPage() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const isOwner = user?.is_superuser ?? false;

  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [parentId, setParentId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);

  const categoriesQuery = useQuery({
    queryKey: ["categories"],
    queryFn: fetchCategories,
  });

  const invalidate = () => void queryClient.invalidateQueries({ queryKey: ["categories"] });

  const createMutation = useMutation({
    mutationFn: () =>
      createCategory({ name, parent_id: parentId || null, description: null }),
    onSuccess: () => {
      setOpen(false);
      setName("");
      setParentId("");
      invalidate();
    },
    onError: (e) => {
      if (isForbidden(e)) setForbidden(true);
      setError(getErrorMessage(e));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deactivateCategory,
    onSuccess: invalidate,
    onError: (e) => {
      if (isForbidden(e)) setForbidden(true);
      setError(getErrorMessage(e));
    },
  });

  const flatten = (nodes: any[], out: any[] = []): any[] => {
    for (const n of nodes) {
      out.push(n);
      flatten(n.children, out);
    }
    return out;
  };

  if (forbidden) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-destructive">
          No tienes permisos para gestionar categorías.
        </CardContent>
      </Card>
    );
  }

  return (
    <RequireSection section="categorias">
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Categorías</h1>
          <p className="text-sm text-muted-foreground">Árbol jerárquico</p>
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
          <CategoryTree
            nodes={categoriesQuery.data ?? []}
            onDelete={(id) => deleteMutation.mutate(id)}
            canEdit={isOwner}
          />
        </CardContent>
      </Card>

      {open && (
        <Card>
          <CardHeader>
            <CardTitle>Nueva categoría</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Nombre</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Categoría padre</Label>
              <Select value={parentId} onChange={(e) => setParentId(e.target.value)}>
                <option value="">Sin padre (raíz)</option>
                {flatten(categoriesQuery.data ?? []).map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </Select>
            </div>
            <div className="flex gap-2">
              <Button disabled={!name || createMutation.isPending} onClick={() => createMutation.mutate()}>
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