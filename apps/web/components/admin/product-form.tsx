"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, Plus, Trash2, UploadCloud } from "lucide-react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { useAuth } from "@/hooks/use-auth";
import {
  addProductImage,
  createProduct,
  fetchAttributes,
  fetchBrands,
  fetchCategories,
  removeProductImage,
  updateProduct,
} from "@/lib/catalog-api";
import { getErrorMessage } from "@/lib/api";
import { flattenCategories } from "@/lib/catalog-utils";
import type { Product } from "@/lib/types";

const productSchema = z.object({
  name: z.string().min(1, "El nombre es obligatorio"),
  short_description: z.string().optional(),
  description: z.string().optional(),
  category_id: z.string().optional(),
  brand_id: z.string().optional(),
  cost_price: z.coerce.number().min(0),
  sale_price: z.coerce.number().positive("Debe ser mayor a 0"),
  currency: z.enum(["PEN", "USD"]),
  price_rule: z.enum([
    "FIXED_PEN",
    "FIXED_USD",
    "USD_CONVERTED",
    "COST_USD_MARGIN",
    "MANUAL",
  ]),
  stock_minimum: z.coerce.number().int().min(0),
  is_serialized: z.boolean(),
  weight_kg: z.string().optional(),
  notes: z.string().optional(),
});

type ProductFormValues = z.infer<typeof productSchema>;

interface ProductFormProps {
  mode: "create" | "edit";
  product?: Product;
}

interface AttributeRow {
  key: string;
  attribute_id: string;
  value: string;
}

function buildPayload(
  values: ProductFormValues,
  attributes: AttributeRow[]
): Record<string, unknown> {
  return {
    name: values.name,
    short_description: values.short_description || null,
    description: values.description || null,
    category_id: values.category_id || null,
    brand_id: values.brand_id || null,
    cost_price: values.cost_price,
    sale_price: values.sale_price,
    currency: values.currency,
    price_rule: values.price_rule,
    stock_minimum: values.stock_minimum,
    is_serialized: values.is_serialized,
    weight_kg: values.weight_kg ? Number(values.weight_kg) : null,
    notes: values.notes || null,
    attributes: attributes
      .filter((row) => row.attribute_id && row.value)
      .map((row) => ({ attribute_id: row.attribute_id, value: row.value })),
  };
}

export function ProductForm({ mode, product }: ProductFormProps) {
  const router = useRouter();
  const { user } = useAuth();
  const isOwner = user?.is_superuser === true;

  const categoriesQuery = useQuery({
    queryKey: ["categories"],
    queryFn: fetchCategories,
  });
  const brandsQuery = useQuery({
    queryKey: ["brands"],
    queryFn: fetchBrands,
  });
  const attributesQuery = useQuery({
    queryKey: ["attributes"],
    queryFn: fetchAttributes,
  });

  const { register, handleSubmit, watch, formState: { errors } } = useForm<ProductFormValues>({
    resolver: zodResolver(productSchema),
    defaultValues: product
      ? {
          name: product.name,
          short_description: product.short_description ?? "",
          description: product.description ?? "",
          category_id: product.category_id ?? "",
          brand_id: product.brand_id ?? "",
          cost_price: Number(product.cost_price),
          sale_price: Number(product.sale_price),
          currency: (product.currency as "PEN" | "USD") ?? "PEN",
          price_rule: product.price_rule,
          stock_minimum: product.stock_minimum,
          is_serialized: product.is_serialized,
          weight_kg: product.weight_kg ?? "",
          notes: product.notes ?? "",
        }
      : {
          name: "",
          short_description: "",
          description: "",
          category_id: "",
          brand_id: "",
          cost_price: 0,
          sale_price: 0,
          currency: "PEN",
          price_rule: "FIXED_PEN",
          stock_minimum: 0,
          is_serialized: false,
          weight_kg: "",
          notes: "",
        },
  });

  const [attributes, setAttributes] = useState<AttributeRow[]>(
    product?.attributes
      ? product.attributes.map((attr) => ({
          key: crypto.randomUUID(),
          attribute_id: attr.attribute_id,
          value: attr.value,
        }))
      : []
  );
  const [images, setImages] = useState(product?.images ?? []);
  const [error, setError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const isSerialized = watch("is_serialized");
  const isOwnerVisible = isOwner || mode === "create";

  const saveMutation = useMutation({
    mutationFn: async (values: ProductFormValues) => {
      const payload = buildPayload(values, attributes);
      const saved = product
        ? await updateProduct(product.id, payload)
        : await createProduct(payload);
      if (attributes.length && product) {
        // En creación los atributos se incluyen en el payload
      }
      return saved;
    },
    onSuccess: (saved) => {
      router.push(`/admin/productos/${saved.id}`);
      router.refresh();
    },
    onError: (e) => setSubmitError(getErrorMessage(e)),
  });

  const imageMutation = useMutation({
    mutationFn: ({ file }: { file: File }) => addProductImage(product!.id, file),
    onSuccess: () => {
      router.refresh();
      window.location.reload();
    },
    onError: (e) => setError(getErrorMessage(e)),
  });

  const removeImageMutation = useMutation({
    mutationFn: (imageId: string) => removeProductImage(product!.id, imageId),
    onSuccess: () => {
      window.location.reload();
    },
    onError: (e) => setError(getErrorMessage(e)),
  });

  const categories = useMemo(
    () => flattenCategories(categoriesQuery.data ?? []),
    [categoriesQuery.data]
  );

  const addAttributeRow = () =>
    setAttributes((prev) => [
      ...prev,
      { key: crypto.randomUUID(), attribute_id: "", value: "" },
    ]);

  const updateAttributeRow = (key: string, patch: Partial<AttributeRow>) =>
    setAttributes((prev) =>
      prev.map((row) => (row.key === key ? { ...row, ...patch } : row))
    );

  const removeAttributeRow = (key: string) =>
    setAttributes((prev) => prev.filter((row) => row.key !== key));

  return (
    <form
      onSubmit={handleSubmit((values) => saveMutation.mutate(values))}
      className="space-y-6"
    >
      {submitError && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {submitError}
        </p>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Información básica</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Nombre *</Label>
            <Input id="name" {...register("name")} />
            {errors.name && (
              <p className="text-sm text-destructive">{errors.name.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="short_description">Descripción corta</Label>
            <Input id="short_description" {...register("short_description")} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="description">Descripción completa</Label>
            <textarea
              id="description"
              className="flex min-h-24 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              {...register("description")}
            />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="category_id">Categoría</Label>
              <Select id="category_id" {...register("category_id")}>
                <option value="">Sin categoría</option>
                {categories.map(({ category, depth }) => (
                  <option key={category.id} value={category.id}>
                    {"\u00A0".repeat(depth * 2)}
                    {category.name}
                  </option>
                ))}
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="brand_id">Marca</Label>
              <Select id="brand_id" {...register("brand_id")}>
                <option value="">Sin marca</option>
                {(brandsQuery.data ?? []).map((brand) => (
                  <option key={brand.id} value={brand.id}>
                    {brand.name}
                  </option>
                ))}
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Precios</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          <div className="space-y-2">
            <Label htmlFor="cost_price">Costo</Label>
            <Input
              id="cost_price"
              type="number"
              step="0.01"
              disabled={!isOwnerVisible}
              {...register("cost_price")}
            />
            {errors.cost_price && (
              <p className="text-sm text-destructive">
                {errors.cost_price.message}
              </p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="sale_price">Precio de venta *</Label>
            <Input
              id="sale_price"
              type="number"
              step="0.01"
              {...register("sale_price")}
            />
            {errors.sale_price && (
              <p className="text-sm text-destructive">
                {errors.sale_price.message}
              </p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="currency">Moneda</Label>
            <Select id="currency" {...register("currency")}>
              <option value="PEN">Soles (PEN)</option>
              <option value="USD">Dólares (USD)</option>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="price_rule">Regla de precio</Label>
            <Select id="price_rule" {...register("price_rule")}>
              <option value="FIXED_PEN">Fijo S/</option>
              <option value="FIXED_USD">Fijo $</option>
              <option value="USD_CONVERTED">Convertido USD→PEN</option>
              <option value="COST_USD_MARGIN">Costo USD + margen</option>
              <option value="MANUAL">Manual</option>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="stock_minimum">Stock mínimo</Label>
            <Input
              id="stock_minimum"
              type="number"
              min={0}
              {...register("stock_minimum")}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Detalles</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="weight_kg">Peso (kg)</Label>
              <Input
                id="weight_kg"
                type="number"
                step="0.001"
                {...register("weight_kg")}
              />
            </div>
            <div className="flex items-end space-y-2">
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" {...register("is_serialized")} />
                Producto serializado
              </label>
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="notes">Notas internas</Label>
            <textarea
              id="notes"
              className="flex min-h-20 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              {...register("notes")}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Atributos dinámicos</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {attributes.length === 0 && (
            <p className="text-sm text-muted-foreground">
              Sin atributos asignados.
            </p>
          )}
          {attributes.map((row) => (
            <div key={row.key} className="grid grid-cols-[1fr_1fr_auto] gap-2">
              <Select
                value={row.attribute_id}
                onChange={(e) =>
                  updateAttributeRow(row.key, { attribute_id: e.target.value })
                }
              >
                <option value="">Atributo</option>
                {(attributesQuery.data ?? []).map((attribute) => (
                  <option key={attribute.id} value={attribute.id}>
                    {attribute.name}
                  </option>
                ))}
              </Select>
              <Input
                placeholder="Valor (ej. 8GB, Negro)"
                value={row.value}
                onChange={(e) =>
                  updateAttributeRow(row.key, { value: e.target.value })
                }
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={() => removeAttributeRow(row.key)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
          <Button type="button" variant="outline" size="sm" onClick={addAttributeRow}>
            <Plus className="mr-1 h-4 w-4" />
            Agregar atributo
          </Button>
        </CardContent>
      </Card>

      {product && (
        <Card>
          <CardHeader>
            <CardTitle>Imágenes</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex flex-wrap gap-3">
              {images.map((image) => (
                <div key={image.id} className="relative">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={image.url ?? ""}
                    alt={product.name}
                    className="h-24 w-24 rounded-md border object-cover"
                  />
                  {image.is_primary && (
                    <span className="absolute left-1 top-1 rounded bg-primary px-1 text-[10px] text-primary-foreground">
                      Principal
                    </span>
                  )}
                  <Button
                    type="button"
                    variant="destructive"
                    size="icon"
                    className="absolute right-1 top-1 h-6 w-6"
                    onClick={() => removeImageMutation.mutate(image.id)}
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              ))}
            </div>
            <label className="inline-flex cursor-pointer items-center gap-2 rounded-md border border-input px-4 py-2 text-sm hover:bg-accent">
              <UploadCloud className="h-4 w-4" />
              Subir imagen
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp,image/gif"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) imageMutation.mutate({ file });
                }}
              />
            </label>
            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}
          </CardContent>
        </Card>
      )}

      <div className="flex justify-end gap-2">
        <Button
          type="button"
          variant="outline"
          onClick={() => router.back()}
        >
          Cancelar
        </Button>
        <Button type="submit" disabled={saveMutation.isPending}>
          {saveMutation.isPending && (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          )}
          {product ? "Guardar cambios" : "Crear producto"}
        </Button>
      </div>
    </form>
  );
}