"use client";

import { ShoppingCart } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { useCart } from "@/features/cart/cart-context";

export function PublicHeader() {
  const { count } = useCart();

  return (
    <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
        <Link href="/" className="font-semibold">
          Inversiones Hasbun
        </Link>
        <nav className="flex items-center gap-4">
          <Link href="/tienda" className="text-sm text-muted-foreground hover:text-foreground">
            Tienda
          </Link>
          <Button asChild variant="outline" size="sm">
            <Link href="/carrito">
              <ShoppingCart className="mr-1 h-4 w-4" />
              Carrito
              {count > 0 && (
                <span className="ml-1 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-primary px-1 text-xs font-semibold text-primary-foreground">
                  {count}
                </span>
              )}
            </Link>
          </Button>
        </nav>
      </div>
    </header>
  );
}