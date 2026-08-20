"use client";

import { useDeferredValue, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Eye, Loader2, Pencil, Plus, Trash2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
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
import { useAuth } from "@/hooks/use-auth";
import {
  deactivateProduct,
  fetchBrands,
  fetchCategories,
  fetchProducts,
  publishProduct,
  unpublishProduct,
} from "@/lib/catalog-api";
import { getErrorMessage } from "@/lib/api";
import { flattenCategories, formatPrice } from "@/lib/catalog-utils";

export default function ProductosPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user } = useAuth();

  const isOwner = user?.is_superuser === true;
  const [search, setSearch] = useState("");
  const deferredSearch = useDeferredValue(search);
  const [categoryId, setCategoryId] = useState("");
  const [brandId, setBrandId] = useState("");
  const [active, setActive] = useState("");
  const [published, setPublished] = useState("");
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const categoriesQuery = useQuery({
    queryKey: ["categories"],
    queryFn: fetchCategories,
  });
  const brandsQuery = useQuery({
    queryKey: ["brands"],
    queryFn: fetchBrands,
  });
  const productsQuery = useQuery({
    queryKey: [
      "products",
      "admin",
      deferredSearch,
      categoryId,
      brandId,
      active,
      published,
      offset,
    ],
    queryFn: () =>
      fetchProducts({
        search: deferredSearch || undefined,
        category_id: categoryId || undefined,
        brand_id: brandId || undefined,
        active: active === "" ? undefined : active === "true",
        published: published === "" ? undefined : published === "true",
        offset,
        limit: 10,
      }),
  });

  useEffect(() => {
    setOffset(0);
  }, [deferredSearch, categoryId, brandId, active, published]);

  const invalidate = () =>
    void queryClient.invalidateQueries({ queryKey: ["products", "admin"] });

  const publishMutation = useMutation({
    mutationFn: publishProduct,
    onSuccess: invalidate,
    onError: (e) => setError(getErrorMessage(e)),
  });
  const unpublishMutation = useMutation({
    mutationFn: unpublishProduct,
    onSuccess: invalidate,
    onError: (e) => setError(getErrorMessage(e)),
  });
  const deactivateMutation = useMutation({
    mutationFn: deactivateProduct,
    onSuccess: invalidate,
    onError: (e) => setError(getErrorMessage(e)),
  });

  const categories = flattenCategories(categoriesQuery.data ?? []);
  const products = productsQuery.data?.items ?? [];
  const total = productsQuery.data?.total ?? 0;
  const pageSize = 10;
  const pages = Math.ceil(total / pageSize);

  const stockBadge = (product: { stock_minimum: number }) =>
    product.stock_minimum > 0 ? (
      <Badge variant="destructive">Stock bajo</Badge>
    ) : null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Productos</h1>
          <p className="text-sm text-muted-foreground">{total} productos</p>
        </div>
        {isOwner && (
          <Button onClick={() => router.push("/admin/productos/nuevo")}>
            <Plus className="mr-2 h-4 w-4" />
            Nuevo producto
          </Button>
        )}
      </div>

      {error && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      <Card>
        <CardContent className="p-4">
          <div className="grid gap-3 md:grid-cols-5">
            <Input
              placeholder="Buscar por nombre, SKU o código..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <Select
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
            >
              <option value="">Todas las categorías</option>
              {categories.map(({ category, depth }) => (
                <option key={category.id} value={category.id}>
                  {"\u00A0".repeat(depth * 2)}
                  {category.name}
                </option>
              ))}
            </Select>
            <Select value={brandId} onChange={(e) => setBrandId(e.target.value)}>
              <option value="">Todas las marcas</option>
              {(brandsQuery.data ?? []).map((brand) => (
                <option key={brand.id} value={brand.id}>
                  {brand.name}
                </option>
              ))}
            </Select>
            <Select value={active} onChange={(e) => setActive(e.target.value)}>
              <option value="">Activo/Inactivo</option>
              <option value="true">Activo</option>
              <option value="false">Inactivo</option>
            </Select>
            <Select
              value={published}
              onChange={(e) => setPublished(e.target.value)}
            >
              <option value="">Publicado/No</option>
              <option value="true">Publicado</option>
              <option value="false">No publicado</option>
            </Select>
          </div>
        </CardContent>
      </Card>

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
                  <TableHead>Producto</TableHead>
                  <TableHead>SKU</TableHead>
                  <TableHead>Marca</TableHead>
                  <TableHead>Categoría</TableHead>
                  <TableHead className="text-right">Precio</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead className="text-right">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {products.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="py-10 text-center text-sm text-muted-foreground">
                      Sin productos
                    </TableCell>
                  </TableRow>
                ) : (
                  products.map((product) => (
                    <TableRow key={product.id}>
                      <TableCell>
                        <Link
                          href={`/admin/productos/${product.id}`}
                          className="font-medium hover:underline"
                        >
                          {product.name}
                        </Link>
                        {stockBadge(product)}
                      </TableCell>
                      <TableCell className="font-mono text-xs">{product.sku}</TableCell>
                      <TableCell>{product.brand_name ?? "—"}</TableCell>
                      <TableCell>{product.category_name ?? "—"}</TableCell>
                      <TableCell className="text-right">
                        {formatPrice(product.current_price)}
                        {product.active_offer && (
                          <span className="block text-xs text-emerald-600">
                            Oferta
                          </span>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          <Badge variant={product.active ? "success" : "destructive"}>
                            {product.active ? "Activo" : "Inactivo"}
                          </Badge>
                          <Badge variant={product.published ? "default" : "secondary"}>
                            {product.published ? "Publicado" : "Borrador"}
                          </Badge>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button asChild variant="ghost" size="sm">
                            <Link href={`/admin/productos/${product.id}`}>
                              <Eye className="h-4 w-4" />
                            </Link>
                          </Button>
                          {isOwner && (
                            <>
                              <Button
                                asChild
                                variant="ghost"
                                size="sm"
                              >
                                <Link href={`/admin/productos/${product.id}/editar`}>
                                  <Pencil className="h-4 w-4" />
                                </Link>
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() =>
                                  product.published
                                    ? unpublishMutation.mutate(product.id)
                                    : publishMutation.mutate(product.id)
                                }
                              >
                                {product.published ? "Despublicar" : "Publicar"}
                              </Button>
                              {product.active && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() =>
                                    deactivateMutation.mutate(product.id)
                                  }
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              )}
                            </>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {pages > 1 && (
        <div className="flex items-center justify-between">
          <Button
            variant="outline"
            size="sm"
            disabled={offset === 0}
            onClick={() => setOffset((o) => Math.max(0, o - pageSize))}
          >
            Anterior
          </Button>
          <span className="text-sm text-muted-foreground">
            Página {Math.floor(offset / pageSize) + 1} de {pages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={offset + pageSize >= total}
            onClick={() => setOffset((o) => o + pageSize)}
          >
            Siguiente
          </Button>
        </div>
      )}
    </div>
  );
}