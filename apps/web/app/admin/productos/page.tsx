"use client";

import { useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Plus, Search } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
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
  deactivateProduct,
  fetchBrands,
  fetchCategoriesFlat,
  fetchProducts,
  publishProduct,
  unpublishProduct,
} from "@/lib/catalog-api";
import { getErrorMessage, isForbidden } from "@/lib/api";
import { useAuth } from "@/hooks/use-auth";

export default function ProductosPage() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const isOwner = user?.is_superuser ?? false;

  const [search, setSearch] = useState("");
  const [debounced, setDebounced] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [brandId, setBrandId] = useState("");
  const [status, setStatus] = useState("");
  const [publish, setPublish] = useState("");
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);

  const categoriesQuery = useQuery({
    queryKey: ["categories-flat"],
    queryFn: fetchCategoriesFlat,
  });
  const brandsQuery = useQuery({
    queryKey: ["brands"],
    queryFn: fetchBrands,
  });
  const productsQuery = useQuery({
    queryKey: [
      "products-admin",
      debounced,
      categoryId,
      brandId,
      status,
      publish,
      page,
    ],
    queryFn: () =>
      fetchProducts({
        admin: true,
        search: debounced || undefined,
        category_id: categoryId || undefined,
        brand_id: brandId || undefined,
        active: status === "" ? undefined : status === "active",
        published: publish === "" ? undefined : publish === "published",
        page,
        per_page: 15,
      }),
  });

  const invalidate = () =>
    void queryClient.invalidateQueries({ queryKey: ["products-admin"] });

  const deactivateMutation = useMutation({
    mutationFn: deactivateProduct,
    onSuccess: invalidate,
    onError: (e) => {
      if (isForbidden(e)) setForbidden(true);
      setError(getErrorMessage(e));
    },
  });
  const publishMutation = useMutation({
    mutationFn: ({ id, published }: { id: string; published: boolean }) =>
      published ? publishProduct(id) : unpublishProduct(id),
    onSuccess: invalidate,
    onError: (e) => {
      if (isForbidden(e)) setForbidden(true);
      setError(getErrorMessage(e));
    },
  });

  const handleSearch = () => {
    window.setTimeout(() => setDebounced(search), 300);
  };
  const syncSearch = (value: string) => {
    setSearch(value);
    window.clearTimeout((window as any)._debounce);
    (window as any)._debounce = window.setTimeout(() => setDebounced(value), 300);
  };

  if (forbidden) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-destructive">
          No tienes permisos para gestionar productos.
        </CardContent>
      </Card>
    );
  }

  const totalPages = Math.max(
    1,
    Math.ceil((productsQuery.data?.total ?? 0) / 15)
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Productos</h1>
          <p className="text-sm text-muted-foreground">
            {productsQuery.data?.total ?? 0} productos
          </p>
        </div>
        {isOwner && (
          <Button asChild>
            <Link href="/admin/productos/nuevo">
              <Plus className="mr-2 h-4 w-4" />
              Nuevo producto
            </Link>
          </Button>
        )}
      </div>

      {error && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      <div className="flex flex-wrap gap-2">
        <div className="relative min-w-[220px] flex-1">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            className="pl-8"
            placeholder="Buscar por nombre, SKU o código de barras…"
            value={search}
            onChange={(e) => syncSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          />
        </div>
        <Select value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
          <option value="">Todas las categorías</option>
          {(categoriesQuery.data ?? []).map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </Select>
        <Select value={brandId} onChange={(e) => setBrandId(e.target.value)}>
          <option value="">Todas las marcas</option>
          {(brandsQuery.data ?? []).map((b) => (
            <option key={b.id} value={b.id}>
              {b.name}
            </option>
          ))}
        </Select>
        <Select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">Activo/Inactivo</option>
          <option value="active">Activos</option>
          <option value="inactive">Inactivos</option>
        </Select>
        <Select value={publish} onChange={(e) => setPublish(e.target.value)}>
          <option value="">Publicados/No</option>
          <option value="published">Publicados</option>
          <option value="unpublished">No publicados</option>
        </Select>
      </div>

      <Card>
        <CardContent className="p-0">
          {productsQuery.isLoading ? (
            <div className="flex justify-center py-10">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Imagen</TableHead>
                  <TableHead>SKU</TableHead>
                  <TableHead>Nombre</TableHead>
                  <TableHead>Marca/Categoría</TableHead>
                  <TableHead>Precio</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead className="text-right">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(productsQuery.data?.items ?? []).map((p) => {
                  const lowStock = p.stock_minimum > 0;
                  return (
                    <TableRow key={p.id}>
                      <TableCell>
                        {p.images?.[0]?.url ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img
                            src={p.images[0].url}
                            alt={p.name}
                            className="h-10 w-10 rounded object-cover"
                          />
                        ) : (
                          <div className="h-10 w-10 rounded bg-muted" />
                        )}
                      </TableCell>
                      <TableCell className="font-mono text-xs">{p.sku}</TableCell>
                      <TableCell className="font-medium">{p.name}</TableCell>
                      <TableCell>
                        <span className="text-xs text-muted-foreground">
                          {p.brand_name ?? "—"} · {p.category_name ?? "—"}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="font-semibold">
                          S/ {p.current_price ?? p.sale_price}
                        </span>
                        <span className="block text-xs text-muted-foreground">
                          costo: S/ {p.cost_price}
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          <Badge variant={p.active ? "success" : "destructive"}>
                            {p.active ? "Activo" : "Inactivo"}
                          </Badge>
                          <Badge variant={p.published ? "default" : "secondary"}>
                            {p.published ? "Publicado" : "Borrador"}
                          </Badge>
                          {lowStock && (
                            <Badge variant="destructive">Stock bajo</Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button variant="ghost" size="sm" asChild>
                            <Link href={`/admin/productos/${p.id}`}>Ver</Link>
                          </Button>
                          {isOwner && (
                            <>
                              <Button variant="ghost" size="sm" asChild>
                                <Link href={`/admin/productos/${p.id}/editar`}>
                                  Editar
                                </Link>
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() =>
                                  publishMutation.mutate({
                                    id: p.id,
                                    published: !p.published,
                                  })
                                }
                              >
                                {p.published ? "Despublicar" : "Publicar"}
                              </Button>
                              {p.active && (
                                <Button
                                  variant="destructive"
                                  size="sm"
                                  onClick={() =>
                                    deactivateMutation.mutate(p.id)
                                  }
                                >
                                  Desactivar
                                </Button>
                              )}
                            </>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
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
  );
}