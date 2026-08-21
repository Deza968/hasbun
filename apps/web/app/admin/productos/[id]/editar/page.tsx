"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Plus, X, UploadCloud } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import {
  attachImage,
  createProduct,
  fetchBrands,
  fetchCategoriesFlat,
  fetchProduct,
  updateProduct,
  uploadFile,
} from "@/lib/catalog-api";
import { getErrorMessage, isForbidden } from "@/lib/api";
import { useAuth } from "@/hooks/use-auth";
import { RequireSection } from "@/components/guards";

interface AttrField {
  attribute: string;
  value: string;
}

export default function ProductoFormPage() {
  const { id } = useParams<{ id: string }>();
  const editing = Boolean(id);
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const isOwner = user?.is_superuser ?? false;

  const [forbidden, setForbidden] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [barcode, setBarcode] = useState("");
  const [shortDescription, setShortDescription] = useState("");
  const [description, setDescription] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [brandId, setBrandId] = useState("");
  const [costPrice, setCostPrice] = useState("0.00");
  const [salePrice, setSalePrice] = useState("0.00");
  const [currency, setCurrency] = useState("PEN");
  const [priceRule, setPriceRule] = useState("MANUAL");
  const [stockMinimum, setStockMinimum] = useState("0");
  const [isSerialized, setIsSerialized] = useState(false);
  const [published, setPublished] = useState(false);
  const [attrs, setAttrs] = useState<AttrField[]>([]);
  const [images, setImages] = useState<{ fileId: string; name: string }[]>([]);
  const [uploading, setUploading] = useState(false);

  const categoriesQuery = useQuery({
    queryKey: ["categories-flat"],
    queryFn: fetchCategoriesFlat,
  });
  const brandsQuery = useQuery({
    queryKey: ["brands"],
    queryFn: fetchBrands,
  });

  const existingQuery = useQuery({
    queryKey: ["product", id],
    queryFn: () => fetchProduct(id),
    enabled: editing,
  });

  useEffect(() => {
    if (existingQuery.data && editing) {
      const p = existingQuery.data;
      setName(p.name);
      setBarcode(p.barcode ?? "");
      setShortDescription(p.short_description ?? "");
      setDescription(p.description ?? "");
      setCategoryId(p.category_id ?? "");
      setBrandId(p.brand_id ?? "");
      setCostPrice(p.cost_price);
      setSalePrice(p.sale_price);
      setCurrency(p.currency);
      setPriceRule(p.price_rule);
      setStockMinimum(String(p.stock_minimum));
      setIsSerialized(p.is_serialized);
      setPublished(p.published);
      setAttrs(p.attributes.map((a) => ({ attribute: a.attribute, value: a.value })));
    }
  }, [existingQuery.data, editing]);

  const infiniteCategories = useMemo(() => categoriesQuery.data ?? [], [
    categoriesQuery.data,
  ]);

  const getCategoryName = (cname: string | null) => cname ?? "Sin categoría";

  const saveMutation = useMutation({
    mutationFn: async () => {
      const payload = {
        name,
        barcode: barcode || null,
        short_description: shortDescription || null,
        description: description || null,
        category_id: categoryId || null,
        brand_id: brandId || null,
        cost_price: costPrice,
        sale_price: salePrice,
        currency,
        price_rule: priceRule,
        stock_minimum: Number(stockMinimum),
        is_serialized: isSerialized,
        published,
        attribute_links: attrs.filter((a) => a.attribute && a.value),
      };
      if (editing) {
        await updateProduct(id, payload);
        for (const img of images) {
          await attachImage(id, img.fileId);
        }
      } else {
        const created = await createProduct(payload);
        for (const img of images) {
          await attachImage(created.id, img.fileId);
        }
        return created;
      }
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["products-admin"] });
      router.push("/admin/productos");
    },
    onError: (e) => {
      if (isForbidden(e)) setForbidden(true);
      setError(getErrorMessage(e));
    },
  });

  const handleFiles = async (files: FileList | null) => {
    if (!files) return;
    setUploading(true);
    setError(null);
    try {
      for (const file of Array.from(files)) {
        const uploaded = await uploadFile(file);
        setImages((prev) => [...prev, { fileId: uploaded.id, name: uploaded.original_name }]);
      }
    } catch (e) {
      setError(getErrorMessage(e));
    } finally {
      setUploading(false);
    }
  };

  if (editing && existingQuery.isLoading) {
    return (
      <div className="flex justify-center py-10">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (forbidden) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-destructive">
          No tienes permisos para crear/editar productos.
        </CardContent>
      </Card>
    );
  }

  return (
    <RequireSection section="productos">
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">
          {editing ? "Editar producto" : "Nuevo producto"}
        </h1>
        <Button onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending}>
          {saveMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Guardar
        </Button>
      </div>

      {error && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Información básica</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Nombre</Label>
                <Input value={name} onChange={(e) => setName(e.target.value)} />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Código de barras</Label>
                  <Input value={barcode} onChange={(e) => setBarcode(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label>Stock mínimo</Label>
                  <Input
                    type="number"
                    value={stockMinimum}
                    onChange={(e) => setStockMinimum(e.target.value)}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Descripción corta</Label>
                <Input
                  value={shortDescription}
                  onChange={(e) => setShortDescription(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Descripción completa</Label>
                <textarea
                  className="min-h-[100px] w-full rounded-md border bg-transparent p-2 text-sm"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Categoría</Label>
                  <Select value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
                    <option value="">Sin categoría</option>
                    {infiniteCategories.map((c) => (
                      <option key={c.id} value={c.id}>
                        {getCategoryName(c.name)}
                      </option>
                    ))}
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Marca</Label>
                  <Select value={brandId} onChange={(e) => setBrandId(e.target.value)}>
                    <option value="">Sin marca</option>
                    {(brandsQuery.data ?? []).map((b) => (
                      <option key={b.id} value={b.id}>
                        {b.name}
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
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-3">
                <div className="space-y-2">
                  <Label>Costo (solo OWNER)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    disabled={!isOwner}
                    value={costPrice}
                    onChange={(e) => setCostPrice(e.target.value)}
                  />
                  {!isOwner && (
                    <p className="text-xs text-muted-foreground">Solo el OWNER ve/edita el costo.</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label>Precio de venta</Label>
                  <Input
                    type="number"
                    step="0.01"
                    disabled={!isOwner}
                    value={salePrice}
                    onChange={(e) => setSalePrice(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Moneda</Label>
                  <Select value={currency} onChange={(e) => setCurrency(e.target.value)}>
                    <option value="PEN">PEN (S/)</option>
                    <option value="USD">USD ($)</option>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Regla de precio</Label>
                <Select value={priceRule} onChange={(e) => setPriceRule(e.target.value)}>
                  <option value="MANUAL">Manual</option>
                  <option value="FIXED_PEN">Fijo en soles</option>
                  <option value="FIXED_USD">Fijo en dólares</option>
                  <option value="USD_CONVERTED">USD convertido (TC del día)</option>
                  <option value="COST_USD_MARGIN">Costo USD + margen</option>
                </Select>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Publicación</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={published} onChange={(e) => setPublished(e.target.checked)} />
                Publicado en tienda
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={isSerialized} onChange={(e) => setIsSerialized(e.target.checked)} />
                Producto serializado (n.º de serie)
              </label>
              {isSerialized && (
                <p className="text-xs text-muted-foreground">
                  Podrás registrar seriales desde el detalle del producto.
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Atributos dinámicos</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {attrs.map((a, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <Input
                    placeholder="Atributo (ej: RAM)"
                    value={a.attribute}
                    onChange={(e) =>
                      setAttrs((prev) =>
                        prev.map((item, i) => (i === idx ? { ...item, attribute: e.target.value } : item))
                      )
                    }
                  />
                  <Input
                    placeholder="Valor (ej: 8GB)"
                    value={a.value}
                    onChange={(e) =>
                      setAttrs((prev) =>
                        prev.map((item, i) => (i === idx ? { ...item, value: e.target.value } : item))
                      )
                    }
                  />
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setAttrs((prev) => prev.filter((_, i) => i !== idx))}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
              <Button
                variant="outline"
                size="sm"
                onClick={() => setAttrs((prev) => [...prev, { attribute: "", value: "" }])}
              >
                <Plus className="mr-1 h-4 w-4" /> Agregar atributo
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Imágenes</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <label className="flex cursor-pointer flex-col items-center gap-2 rounded-md border border-dashed p-6 text-sm text-muted-foreground">
                <UploadCloud className="h-6 w-6" />
                Arrastra imágenes o haz clic
                <input
                  type="file"
                  multiple
                  accept="image/jpeg,image/png,image/webp"
                  className="hidden"
                  onChange={(e) => void handleFiles(e.target.files)}
                />
              </label>
              {uploading && <Loader2 className="h-4 w-4 animate-spin" />}
              <div className="space-y-2">
                {images.map((img, i) => (
                  <div key={i} className="flex items-center justify-between rounded border p-2 text-sm">
                    <span className="truncate">{img.name}</span>
                    <Badge variant="secondary">Nuevo</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
    </RequireSection>
  );
}