"use client";

import { useQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";

import { ProductForm } from "@/components/admin/product-form";
import { Card, CardContent } from "@/components/ui/card";
import { fetchProduct } from "@/lib/catalog-api";

export default function EditarProductoPage({
  params,
}: {
  params: { id: string };
}) {
  const productQuery = useQuery({
    queryKey: ["products", params.id],
    queryFn: () => fetchProduct(params.id),
  });

  if (productQuery.isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!productQuery.data) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-destructive">
          Producto no encontrado
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Editar: {productQuery.data.name}</h1>
      <ProductForm mode="edit" product={productQuery.data} />
    </div>
  );
}