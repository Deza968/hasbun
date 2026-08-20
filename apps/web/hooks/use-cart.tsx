"use client";

import * as React from "react";

export interface CartItem {
  productId: string;
  name: string;
  slug: string;
  sku: string;
  price: number;
  currency: string;
  quantity: number;
  image?: string | null;
}

const STORAGE_KEY = "hasbun_cart";

export interface CartContextValue {
  items: CartItem[];
  count: number;
  subtotal: number;
  addItem: (item: CartItem) => void;
  removeItem: (productId: string) => void;
  setQuantity: (productId: string, quantity: number) => void;
  clear: () => void;
}

const CartContext = React.createContext<CartContextValue | null>(null);

function readCart(): CartItem[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as CartItem[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeCart(items: CartItem[]) {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

export function CartProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = React.useState<CartItem[]>([]);

  React.useEffect(() => {
    setItems(readCart());
  }, []);

  const save = (next: CartItem[]) => {
    setItems(next);
    writeCart(next);
  };

  const addItem = (item: CartItem) => {
    setItems((prev) => {
      const existing = prev.find((i) => i.productId === item.productId);
      const next = existing
        ? prev.map((i) =>
            i.productId === item.productId
              ? { ...i, quantity: i.quantity + item.quantity }
              : i
          )
        : [...prev, item];
      writeCart(next);
      return next;
    });
  };

  const removeItem = (productId: string) => {
    setItems((prev) => {
      const next = prev.filter((i) => i.productId !== productId);
      writeCart(next);
      return next;
    });
  };

  const setQuantity = (productId: string, quantity: number) => {
    if (quantity <= 0) return removeItem(productId);
    setItems((prev) => {
      const next = prev.map((i) =>
        i.productId === productId ? { ...i, quantity } : i
      );
      writeCart(next);
      return next;
    });
  };

  const clear = () => save([]);

  const count = React.useMemo(
    () => items.reduce((acc, i) => acc + i.quantity, 0),
    [items]
  );
  const subtotal = React.useMemo(
    () => items.reduce((acc, i) => acc + i.price * i.quantity, 0),
    [items]
  );

  const value: CartContextValue = {
    items,
    count,
    subtotal,
    addItem,
    removeItem,
    setQuantity,
    clear,
  };

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart(): CartContextValue {
  const ctx = React.useContext(CartContext);
  if (!ctx) throw new Error("useCart debe usarse dentro de CartProvider");
  return ctx;
}

export function buildWhatsAppLink(
  items: CartItem[],
  subtotal: number,
  config?: { phone?: string; storeName?: string }
): string {
  const phone = config?.phone ?? "51990000001";
  const store = config?.storeName ?? "Inversiones Hasbun";
  const lines = items.map(
    (i) => `${i.quantity} x ${i.name} (S/ ${i.price.toFixed(2)})`
  );
  const text = [
    `Hola ${store}, quisiera comprar:`,
    ...lines,
    `Subtotal: S/ ${subtotal.toFixed(2)}`,
  ].join("\n");
  return `https://wa.me/${phone}?text=${encodeURIComponent(text)}`;
}