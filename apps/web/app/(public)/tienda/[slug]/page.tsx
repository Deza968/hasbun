"use client";

import { useQuery } from "@tanstack/react-query";
import { Loader2, ShoppingCart } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useCart, buildWhatsAppLink } from "@/features/cart/cart-context";
import { fetchPublicProductBySlug } from "@/lib/catalog-api";
import { formatPrice } from "@/lib/catalog-utils";

export default function ProductoPublicoPage({
  params,
}: {
  params: { slug: string };
}) {
  const { add } = useCart();
  const productQuery = useQuery({
    queryKey: ["public-product", params.slug],
    queryFn: () => fetchPublicProductBySlug(params.slug),
  });

  if (productQuery.isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const product = productQuery.data;

  if (!product) {
    return (
      <div className="py-16 text-center text-muted-foreground">
        Producto no encontrado.
      </div>
    );
  }

  const primaryImage = product.images.find((i) => i.is_primary)?.url;
  const offer = product.active_offer;

  const whatsappLink = buildWhatsAppLink(
    [
      {
        productId: product.id,
        sku: product.sku,
        name: product.name,
        slug: product.slug,
        price: product.current_price,
        imageUrl: primaryImage ?? null,
        quantity: 1,
      },
    ],
    Number(product.current_price)
  );

  return (
    <div className="mx-auto max-w-6xl p-4">
      <Link href="/tienda" className="text-sm text-muted-foreground hover:underline">
        ← Volver a la tienda
      </Link>
      <div className="mt-4 grid gap-8 md:grid-cols-2">
        <div className="flex h-80 items-center justify-center rounded-lg bg-muted/30">
          {primaryImage ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={primaryImage} alt={product.name} className="h-full w-full object-contain" />
          ) : (
            <span className="text-6xl text-muted-foreground">📦</span>
          )}
        </div>
        <div className="space-y-4">
          {product.brand_name && (
            <span className="text-sm text-muted-foreground">
              {product.brand_name}
            </span>
          )}
          <h1 className="text-3xl font-bold">{product.name}</h1>
          <div className="flex items-center gap-3">
            {offer && (
              <>
                <span className="text-lg text-muted-foreground line-through">
                  {formatPrice(product.sale_price)}
                </span>
                <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-700">
                  OFERTA
                </span>
              </>
            )}
            <span className="text-3xl font-bold">
              {formatPrice(product.current_price)}
            </span>
          </div>
          {product.short_description && (
            <p className="text-muted-foreground">{product.short_description}</p>
          )}
          {product.description && <p className="text-sm">{product.description}</p>}

          {product.attributes.length > 0 && (
            <Card>
              <CardContent className="grid gap-2 p-4">
                {product.attributes.map((attr) => (
                  <div key={attr.value_id} className="grid grid-cols-2 text-sm">
                    <span className="text-muted-foreground">
                      {attr.attribute_name}
                    </span>
                    <span>{attr.value}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          <div className="flex flex-wrap gap-3 pt-2">
            <Button onClick={() => add(product)}>
              <ShoppingCart className="mr-2 h-4 w-4" />
              Agregar al carrito
            </Button>
            <Button asChild variant="outline">
              <a href={whatsappLink} target="_blank" rel="noopener noreferrer">
                Comprar por WhatsApp
              </a>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}