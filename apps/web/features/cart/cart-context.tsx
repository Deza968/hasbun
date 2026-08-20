"use client";

import * as React from "react";

import type { PublicProduct } from "@/lib/types";

export interface CartItem {
  productId: string;
  sku: string;
  name: string;
  slug: string;
  price: string;
  imageUrl: string | null;
  quantity: number;
}

interface CartContextValue {
  items: CartItem[];
  count: number;
  subtotal: number;
  add: (product: PublicProduct, quantity?: number) => void;
  remove: (productId: string) => void;
  updateQuantity: (productId: string, quantity: number) => void;
  clear: () => void;
}

const CartContext = React.createContext<CartContextValue | null>(null);

const STORAGE_KEY = "hasbun_cart_v1";

function readCart(): CartItem[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as CartItem[]) : [];
  } catch {
    return [];
  }
}

function imageUrl(product: PublicProduct): string | null {
  const primary = product.images.find((img) => img.is_primary) ?? product.images[0];
  return primary?.url ?? null;
}

export function CartProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = React.useState<CartItem[]>([]);

  React.useEffect(() => {
    setItems(readCart());
  }, []);

  React.useEffect(() => {
    if (items.length === 0) {
      window.sessionStorage.removeItem(STORAGE_KEY);
    } else {
      window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    }
  }, [items]);

  const add = React.useCallback((product: PublicProduct, quantity = 1) => {
    setItems((prev) => {
      const existing = prev.find((item) => item.productId === product.id);
      if (existing) {
        return prev.map((item) =>
          item.productId === product.id
            ? { ...item, quantity: item.quantity + quantity }
            : item
        );
      }
      return [
        ...prev,
        {
          productId: product.id,
          sku: product.sku,
          name: product.name,
          slug: product.slug,
          price: product.current_price,
          imageUrl: imageUrl(product),
          quantity,
        },
      ];
    });
  }, []);

  const remove = React.useCallback((productId: string) => {
    setItems((prev) => prev.filter((item) => item.productId !== productId));
  }, []);

  const updateQuantity = React.useCallback((productId: string, quantity: number) => {
    setItems((prev) =>
      prev
        .map((item) =>
          item.productId === productId
            ? { ...item, quantity: Math.max(1, quantity) }
            : item
        )
        .filter((item) => item.quantity > 0)
    );
  }, []);

  const clear = React.useCallback(() => setItems([]), []);

  const subtotal = React.useMemo(
    () =>
      items.reduce(
        (acc, item) => acc + Number(item.price) * item.quantity,
        0
      ),
    [items]
  );
  const count = React.useMemo(
    () => items.reduce((acc, item) => acc + item.quantity, 0),
    [items]
  );

  return (
    <CartContext.Provider
      value={{ items, count, subtotal, add, remove, updateQuantity, clear }}
    >
      {children}
    </CartContext.Provider>
  );
}

export function useCart(): CartContextValue {
  const context = React.useContext(CartContext);
  if (!context) {
    throw new Error("useCart debe usarse dentro de CartProvider");
  }
  return context;
}

export function buildWhatsAppLink(
  items: CartItem[],
  subtotal: number
): string {
  const phone = "51900000001"; // WhatsApp de la tienda (configurable)
  const lines = items.map(
    (item) => `• ${item.name} x${item.quantity} — S/ ${(Number(item.price) * item.quantity).toFixed(2)}`
  );
  const message = encodeURIComponent(
    `Hola Hasbun, quiero pedir:\n${lines.join("\n")}\nTotal: S/ ${subtotal.toFixed(2)}`
  );
  return `https://wa.me/${phone}?text=${message}`;
}