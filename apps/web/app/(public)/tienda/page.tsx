"use client";

import { useDeferredValue, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2, ShoppingCart } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { useCart } from "@/features/cart/cart-context";
import {
  fetchBrands,
  fetchCategories,
  fetchPublicProducts,
} from "@/lib/catalog-api";
import { flattenCategories, formatPrice } from "@/lib/catalog-utils";

export default function TiendaPage() {
  const { add } = useCart();
  const [search, setSearch] = useState("");
  const deferredSearch = useDeferredValue(search);
  const [categoryId, setCategoryId] = useState("");
  const [brandId, setBrandId] = useState("");

  const categoriesQuery = useQuery({
    queryKey: ["categories"],
    queryFn: fetchCategories,
  });
  const brandsQuery = useQuery({
    queryKey: ["brands"],
    queryFn: fetchBrands,
  });
  const productsQuery = useQuery({
    queryKey: ["public-products", deferredSearch, categoryId, brandId],
    queryFn: () =>
      fetchPublicProducts({
        search: deferredSearch || undefined,
        category_id: categoryId || undefined,
        brand_id: brandId || undefined,
        limit: 50,
      }),
  });

  useEffect(() => {}, []);
  const categories = flattenCategories(categoriesQuery.data ?? []);
  const products = productsQuery.data?.items ?? [];

  const image = (url: string | null | undefined) => url ?? null;

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-4">
      <div>
        <h1 className="text-3xl font-bold">Tienda</h1>
        <p className="text-muted-foreground">
          Catálogo de Inversiones Hasbun - Sicuani, Cusco
        </p>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <Input
          placeholder="Buscar producto..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <Select value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
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
      </div>

      {productsQuery.isLoading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : products.length === 0 ? (
        <p className="py-16 text-center text-muted-foreground">
          No hay productos disponibles.
        </p>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {products.map((product) => (
            <Card key={product.id} className="flex flex-col">
              <Link href={`/tienda/${product.slug}`}>
                <div className="flex h-44 items-center justify-center bg-muted/30">
                  {image(product.images.find((i) => i.is_primary)?.url) ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={product.images.find((i) => i.is_primary)?.url ?? ""}
                      alt={product.name}
                      className="h-full w-full object-contain"
                    />
                  ) : (
                    <span className="text-4xl text-muted-foreground">📦</span>
                  )}
                </div>
              </Link>
              <CardHeader className="p-4 pb-0">
                <div className="flex items-center justify-between">
                  {product.brand_name && (
                    <span className="text-xs text-muted-foreground">
                      {product.brand_name}
                    </span>
                  )}
                  {product.active_offer && (
                    <Badge>OFERTA</Badge>
                  )}
                </div>
                <CardTitle className="text-base">
                  <Link href={`/tienda/${product.slug}`} className="hover:underline">
                    {product.name}
                  </Link>
                </CardTitle>
                <CardDescription className="line-clamp-2">
                  {product.short_description}
                </CardDescription>
              </CardHeader>
              <CardFooter className="mt-auto flex items-center justify-between p-4">
                <div>
                  {product.active_offer && (
                    <span className="block text-xs text-muted-foreground line-through">
                      {formatPrice(product.sale_price)}
                    </span>
                  )}
                  <span className="text-lg font-bold">
                    {formatPrice(product.current_price)}
                  </span>
                </div>
                <Button
                  size="sm"
                  onClick={() => add(product)}
                >
                  <ShoppingCart className="mr-1 h-4 w-4" />
                  Agregar
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}