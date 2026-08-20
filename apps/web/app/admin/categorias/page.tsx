"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Plus, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { createCategory, deleteCategory, fetchCategories } from "@/lib/catalog-api";
import { getErrorMessage } from "@/lib/api";
import { flattenCategories } from "@/lib/catalog-utils";
import type { Category } from "@/lib/types";

function CategoryRow({
  category,
  depth,
}: {
  category: Category;
  depth: number;
}) {
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: () => deleteCategory(category.id),
    onSuccess: () =>
      void queryClient.invalidateQueries({ queryKey: ["categories"] }),
    onError: (e) => setDeleteError(getErrorMessage(e)),
  });

  return (
    <div>
      <div
        className="flex items-center justify-between py-2"
        style={{ marginLeft: `${depth * 1.5}rem` }}
      >
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">{category.name}</span>
          {!category.active && (
            <span className="text-xs text-muted-foreground">(inactiva)</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {deleteError && (
            <span className="text-xs text-destructive">{deleteError}</span>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => deleteMutation.mutate()}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>
      {(category.children ?? []).map((child) => (
        <CategoryRow key={child.id} category={child} depth={depth + 1} />
      ))}
    </div>
  );
}

export default function CategoriasPage() {
  const { user } = useAuth();
  const isOwner = user?.is_superuser === true;
  const queryClient = useQueryClient();

  const categoriesQuery = useQuery({
    queryKey: ["categories"],
    queryFn: fetchCategories,
  });

  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [parentId, setParentId] = useState("");
  const [error, setError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: () =>
      createCategory({ name, parent_id: parentId || null }),
    onSuccess: () => {
      setOpen(false);
      setName("");
      setParentId("");
      void queryClient.invalidateQueries({ queryKey: ["categories"] });
    },
    onError: (e) => setError(getErrorMessage(e)),
  });

  const categories = flattenCategories(categoriesQuery.data ?? []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Categorías</h1>
          <p className="text-sm text-muted-foreground">
            Árbol jerárquico del catálogo
          </p>
        </div>
        {isOwner && (
          <Button onClick={() => setOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Nueva categoría
          </Button>
        )}
      </div>

      {error && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Estructura</CardTitle>
        </CardHeader>
        <CardContent>
          {categoriesQuery.isLoading ? (
            <div className="flex justify-center py-10">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <div className="divide-y">
              {(categoriesQuery.data ?? []).map((category) => (
                <CategoryRow key={category.id} category={category} depth={0} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nueva categoría</DialogTitle>
            <DialogDescription>
              Las categorías se organizan en árbol (padre → hijos).
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="catName">Nombre</Label>
              <Input
                id="catName"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="parent">Categoría padre</Label>
              <Select
                id="parent"
                value={parentId}
                onChange={(e) => setParentId(e.target.value)}
              >
                <option value="">Sin padre (raíz)</option>
                {categories.map(({ category, depth }) => (
                  <option key={category.id} value={category.id}>
                    {"\u00A0".repeat(depth * 2)}
                    {category.name}
                  </option>
                ))}
              </Select>
            </div>
            <Button
              className="w-full"
              disabled={!name || createMutation.isPending}
              onClick={() => createMutation.mutate()}
            >
              Crear categoría
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}