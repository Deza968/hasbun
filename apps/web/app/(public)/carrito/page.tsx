"use client";

import { Minus, Plus, ShoppingCart, Trash2 } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { buildWhatsAppLink, useCart } from "@/features/cart/cart-context";
import { formatPrice } from "@/lib/catalog-utils";

export default function CarritoPage() {
  const { items, updateQuantity, remove, subtotal, count, clear } = useCart();

  if (items.length === 0) {
    return (
      <div className="mx-auto max-w-3xl space-y-4 p-4">
        <h1 className="text-2xl font-semibold">Carrito</h1>
        <Card>
          <CardContent className="flex flex-col items-center gap-4 py-16 text-center">
            <ShoppingCart className="h-10 w-10 text-muted-foreground" />
            <p className="text-muted-foreground">Tu carrito está vacío.</p>
            <Button asChild>
              <Link href="/tienda">Ir a la tienda</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const whatsappLink = buildWhatsAppLink(items, subtotal);

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">
          Carrito ({count} {count === 1 ? "producto" : "productos"})
        </h1>
        <Button variant="ghost" size="sm" onClick={clear}>
          Vaciar carrito
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="divide-y">
            {items.map((item) => (
              <div key={item.productId} className="flex items-center gap-4 p-4">
                {item.imageUrl ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={item.imageUrl}
                    alt={item.name}
                    className="h-16 w-16 rounded-md border object-cover"
                  />
                ) : (
                  <div className="flex h-16 w-16 items-center justify-center rounded-md bg-muted/40 text-2xl">
                    📦
                  </div>
                )}
                <div className="flex-1">
                  <Link
                    href={`/tienda/${item.slug}`}
                    className="font-medium hover:underline"
                  >
                    {item.name}
                  </Link>
                  <p className="text-sm text-muted-foreground">
                    {formatPrice(item.price)}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => updateQuantity(item.productId, item.quantity - 1)}
                  >
                    <Minus className="h-4 w-4" />
                  </Button>
                  <span className="w-8 text-center">{item.quantity}</span>
                  <Button
                    variant="outline"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => updateQuantity(item.productId, item.quantity + 1)}
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                <div className="w-24 text-right font-semibold">
                  {formatPrice(Number(item.price) * item.quantity)}
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => remove(item.productId)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Resumen</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between text-lg">
            <span>Subtotal</span>
            <span className="font-bold">{formatPrice(subtotal)}</span>
          </div>
          <p className="text-sm text-muted-foreground">
            El pago se coordina por WhatsApp. El tipo de cambio aplica según el
            día de entrega.
          </p>
          <Button asChild className="w-full">
            <a href={whatsappLink} target="_blank" rel="noopener noreferrer">
              Finalizar compra por WhatsApp
            </a>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}