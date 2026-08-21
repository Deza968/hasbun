"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ShoppingCart } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { fetchBrands, fetchCategoriesFlat, fetchProducts } from "@/lib/catalog-api";
import { useCart } from "@/hooks/use-cart";

function formatPrice(value: string): string {
  const n = Number(value);
  return Number.isFinite(n) ? `S/ ${n.toFixed(2)}` : value;
}

export default function TiendaPage() {
  const [search, setSearch] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [brandId, setBrandId] = useState("");
  const { addItem } = useCart();

  const categoriesQuery = useQuery({
    queryKey: ["categories-flat"],
    queryFn: fetchCategoriesFlat,
  });

  const brandsQuery = useQuery({
    queryKey: ["brands"],
    queryFn: fetchBrands,
  });

  const productsQuery = useQuery({
    queryKey: ["public-products", { search, categoryId, brandId }],
    queryFn: () =>
      fetchProducts({
        search: search || undefined,
        category_id: categoryId || undefined,
        brand_id: brandId || undefined,
        published: true,
        per_page: 50,
      }),
  });

  const products = (productsQuery.data?.items ?? []).filter((p) => p.active);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Tienda</h1>
        <p className="text-sm text-muted-foreground">Productos disponibles</p>
      </div>

      <div className="grid gap-2 sm:grid-cols-3">
        <Input
          placeholder="Buscar por nombre o SKU…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
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
          {(brandsQuery.data ?? [])
            .filter((b) => b.active)
            .map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
        </Select>
      </div>

      {productsQuery.isLoading ? (
        <p className="py-10 text-center text-sm">Cargando…</p>
      ) : products.length === 0 ? (
        <p className="py-10 text-center text-sm text-muted-foreground">
          No hay productos publicados.
        </p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {products.map((p) => {
            const price = p.current_price ?? p.sale_price;
            return (
              <div key={p.id} className="flex flex-col rounded-lg border p-4">
                <Link href={`/productos/${p.id}`}>
                  <div className="mb-3 flex h-32 items-center justify-center overflow-hidden rounded bg-muted">
                    {p.images?.[0]?.url ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={p.images[0].url}
                        alt={p.name}
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <span className="text-xs text-muted-foreground">Sin imagen</span>
                    )}
                  </div>
                  <h2 className="font-medium line-clamp-2">{p.name}</h2>
                  <p className="text-xs text-muted-foreground">
                    {p.brand_name ?? "Sin marca"}
                    {p.category_name ? ` · ${p.category_name}` : ""}
                  </p>
                </Link>
                <div className="mt-auto pt-3">
                  {p.offers?.some((o) => o.active) && (
                    <p className="text-xs text-muted-foreground line-through">
                      {formatPrice(p.sale_price)}
                    </p>
                  )}
                  <p className="text-lg font-semibold">{formatPrice(price)}</p>
                  <Button
                    className="mt-2 w-full"
                    size="sm"
                    onClick={() =>
                      addItem({
                        productId: p.id,
                        name: p.name,
                        slug: p.slug,
                        sku: p.sku,
                        price: Number(price),
                        currency: p.current_currency ?? p.currency,
                        quantity: 1,
                        image: p.images?.[0]?.url ?? null,
                      })
                    }
                  >
                    <ShoppingCart className="mr-2 h-4 w-4" /> Agregar
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {productsQuery.data && productsQuery.data.total > 50 && (
        <p className="text-center text-xs text-muted-foreground">
          Mostrando los primeros {products.length} de {productsQuery.data.total}.
        </p>
      )}
    </div>
  );
}