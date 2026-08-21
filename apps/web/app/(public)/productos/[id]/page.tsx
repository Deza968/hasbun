"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ChevronLeft, Minus, Plus, ShoppingCart } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { fetchProduct } from "@/lib/catalog-api";
import { useCart } from "@/hooks/use-cart";

function formatPrice(value: string): string {
  const n = Number(value);
  return Number.isFinite(n) ? `S/ ${n.toFixed(2)}` : value;
}

export default function ProductoPublicoPage() {
  const { id } = useParams<{ id: string }>();
  const { addItem } = useCart();
  const [quantity, setQuantity] = useState(1);

  const productQuery = useQuery({
    queryKey: ["public-product", id],
    queryFn: () => fetchProduct(id),
  });

  if (productQuery.isLoading) {
    return <p className="py-10 text-center text-sm">Cargando…</p>;
  }
  if (productQuery.isError || !productQuery.data) {
    return (
      <p className="py-10 text-center text-sm text-muted-foreground">
        Producto no disponible.
      </p>
    );
  }

  const product = productQuery.data;
  const price = product.current_price ?? product.sale_price;
  const hasOffer = product.offers?.some((o) => o.active);

  return (
    <div className="space-y-6">
      <Button variant="ghost" size="sm" asChild>
        <Link href="/">
          <ChevronLeft className="mr-1 h-4 w-4" /> Volver a la tienda
        </Link>
      </Button>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="flex h-72 items-center justify-center overflow-hidden rounded-lg bg-muted">
          {product.images?.[0]?.url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={product.images[0].url}
              alt={product.name}
              className="h-full w-full object-cover"
            />
          ) : (
            <span className="text-sm text-muted-foreground">Sin imagen</span>
          )}
        </div>

        <div className="space-y-4">
          <div>
            <p className="text-xs uppercase tracking-wide text-muted-foreground">
              {product.brand_name ?? "Inversiones Hasbun"}
            </p>
            <h1 className="text-2xl font-semibold">{product.name}</h1>
            {product.short_description && (
              <p className="text-sm text-muted-foreground">{product.short_description}</p>
            )}
          </div>

          <div>
            {hasOffer && (
              <p className="text-sm text-muted-foreground line-through">
                {formatPrice(product.sale_price)}
              </p>
            )}
            <p className="text-3xl font-bold">{formatPrice(price)}</p>
          </div>

          {product.attributes && product.attributes.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {product.attributes.map((a, i) => (
                <Badge key={i} variant="secondary">
                  {a.attribute}: {a.value}
                </Badge>
              ))}
            </div>
          )}

          <div className="flex items-center gap-3">
            <div className="flex items-center rounded border">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setQuantity((q) => Math.max(1, q - 1))}
              >
                <Minus className="h-4 w-4" />
              </Button>
              <span className="w-10 text-center text-sm">{quantity}</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setQuantity((q) => q + 1)}
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            <Button
              className="flex-1"
              onClick={() =>
                addItem({
                  productId: product.id,
                  name: product.name,
                  slug: product.slug,
                  sku: product.sku,
                  price: Number(price),
                  currency: product.current_currency ?? product.currency,
                  quantity,
                  image: product.images?.[0]?.url ?? null,
                })
              }
            >
              <ShoppingCart className="mr-2 h-4 w-4" /> Agregar al carrito
            </Button>
          </div>

          <p className="text-xs text-muted-foreground">
            SKU: <span className="font-mono">{product.sku}</span>
          </p>
        </div>
      </div>

      {product.description && (
        <Card>
          <CardHeader>
            <CardTitle>Descripción</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="whitespace-pre-line text-sm">{product.description}</p>
          </CardContent>
        </Card>
      )}

      {product.images && product.images.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Galería</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-2">
              {product.images.map((img) => (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  key={img.id}
                  src={img.url ?? ""}
                  alt={product.name}
                  className="h-20 w-full rounded object-cover"
                />
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}