"use client";

import Link from "next/link";
import { Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { buildWhatsAppLink, useCart } from "@/hooks/use-cart";

export default function CarritoPage() {
  const { items, subtotal, setQuantity, removeItem, clear } = useCart();

  if (items.length === 0) {
    return (
      <div className="space-y-4 py-10 text-center">
        <p className="text-muted-foreground">Tu carrito está vacío.</p>
        <Button asChild>
          <Link href="/">Ver productos</Link>
        </Button>
      </div>
    );
  }

  const whatsappUrl = buildWhatsAppLink(items, subtotal, {
    phone: "51990000001",
    storeName: "Inversiones Hasbun",
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Carrito</h1>
          <p className="text-sm text-muted-foreground">
            {items.reduce((acc, i) => acc + i.quantity, 0)} artículos
          </p>
        </div>
        <Button variant="ghost" size="sm" onClick={clear}>
          Vaciar
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-2 lg:col-span-2">
          {items.map((item) => (
            <div
              key={item.productId}
              className="flex items-center gap-3 rounded-lg border p-3"
            >
              <div className="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded bg-muted">
                {item.image ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={item.image}
                    alt={item.name}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <span className="text-[10px] text-muted-foreground">Sin imagen</span>
                )}
              </div>
              <div className="min-w-0 flex-1">
                <Link
                  href={`/productos/${item.productId}`}
                  className="line-clamp-1 text-sm font-medium hover:underline"
                >
                  {item.name}
                </Link>
                <p className="text-xs text-muted-foreground">S/ {item.price.toFixed(2)}</p>
              </div>
              <div className="flex items-center gap-1">
                <Button
                  className="h-8 w-8" variant="outline" size="sm"
                  onClick={() => setQuantity(item.productId, item.quantity - 1)}
                >
                  −
                </Button>
                <Input
                  className="h-8 w-14 text-center"
                  value={item.quantity}
                  onChange={(e) => {
                    const n = Number(e.target.value);
                    if (Number.isInteger(n) && n > 0) {
                      setQuantity(item.productId, n);
                    }
                  }}
                />
                <Button
                  className="h-8 w-8" variant="outline" size="sm"
                  onClick={() => setQuantity(item.productId, item.quantity + 1)}
                >
                  +
                </Button>
              </div>
              <p className="w-24 text-right text-sm font-medium">
                S/ {(item.price * item.quantity).toFixed(2)}
              </p>
              <Button
                className="h-8 w-8" variant="ghost" size="sm"
                onClick={() => removeItem(item.productId)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>

        <Card className="h-fit">
          <CardHeader>
            <CardTitle>Resumen</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Subtotal</span>
              <span className="font-semibold">S/ {subtotal.toFixed(2)}</span>
            </div>
            <Button asChild className="w-full">
              <a
                href={whatsappUrl}
                target="_blank"
                rel="noopener noreferrer"
              >
                Confirmar por WhatsApp
              </a>
            </Button>
            <Button asChild variant="outline" className="w-full">
              <Link href="/">Seguir comprando</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}