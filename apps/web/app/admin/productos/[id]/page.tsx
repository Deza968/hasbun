"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronLeft, Plus } from "lucide-react";

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
import {
  createOffer,
  fetchProduct,
  registerSerial,
} from "@/lib/catalog-api";
import { getErrorMessage, isForbidden } from "@/lib/api";
import { useAuth } from "@/hooks/use-auth";
import { RequireSection } from "@/components/guards";

export default function ProductoDetallePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const isOwner = user?.is_superuser ?? false;

  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);
  const [serialOpen, setSerialOpen] = useState(false);
  const [serialNumber, setSerialNumber] = useState("");
  const [serialImei, setSerialImei] = useState("");
  const [offerOpen, setOfferOpen] = useState(false);
  const [normalPrice, setNormalPrice] = useState("");
  const [offerPrice, setOfferPrice] = useState("");

  const productQuery = useQuery({
    queryKey: ["product", id],
    queryFn: () => fetchProduct(id),
  });

  const invalidate = () => void queryClient.invalidateQueries({ queryKey: ["product", id] });

  const serialMutation = useMutation({
    mutationFn: () =>
      registerSerial(id, {
        serial_number: serialNumber,
        imei: serialImei || null,
        status: "AVAILABLE",
      }),
    onSuccess: () => {
      setSerialOpen(false);
      setSerialNumber("");
      setSerialImei("");
      invalidate();
    },
    onError: (e) => {
      if (isForbidden(e)) setForbidden(true);
      setError(getErrorMessage(e));
    },
  });

  const offerMutation = useMutation({
    mutationFn: () => {
      const now = new Date();
      const end = new Date(now.getTime() + 30 * 86400 * 1000);
      return createOffer(id, {
        normal_price: normalPrice,
        offer_price: offerPrice,
        start_at: now.toISOString(),
        end_at: end.toISOString(),
      });
    },
    onSuccess: () => {
      setOfferOpen(false);
      setNormalPrice("");
      setOfferPrice("");
      invalidate();
    },
    onError: (e) => {
      if (isForbidden(e)) setForbidden(true);
      setError(getErrorMessage(e));
    },
  });

  const product = productQuery.data;

  if (productQuery.isLoading) {
    return <p className="py-10 text-center text-sm">Cargando…</p>;
  }
  if (!product) return null;

  return (
    <RequireSection section="productos">
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => router.back()}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-semibold">{product.name}</h1>
            <p className="text-sm text-muted-foreground">
              SKU <span className="font-mono">{product.sku}</span>{" "}
              {product.barcode ? `· EAN ${product.barcode}` : ""}
            </p>
          </div>
        </div>
        {isOwner && (
          <Button asChild variant="outline">
            <Link href={`/admin/productos/${product.id}/editar`}>Editar</Link>
          </Button>
        )}
      </div>

      {error && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Información</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p><span className="text-muted-foreground">Marca:</span> {product.brand_name ?? "—"}</p>
            <p><span className="text-muted-foreground">Categoría:</span> {product.category_name ?? "—"}</p>
            <p><span className="text-muted-foreground">Regla de precio:</span> {product.price_rule}</p>
            <p><span className="text-muted-foreground">Moneda:</span> {product.currency}</p>
            <p>
              <span className="text-muted-foreground">Precio venta:</span>{" "}
              <span className="font-semibold">S/ {product.sale_price}</span>
            </p>
            {isOwner && (
              <p><span className="text-muted-foreground">Costo:</span> S/ {product.cost_price}</p>
            )}
            <div className="flex flex-wrap gap-1 pt-1">
              <Badge variant={product.active ? "success" : "destructive"}>
                {product.active ? "Activo" : "Inactivo"}
              </Badge>
              <Badge variant={product.published ? "default" : "secondary"}>
                {product.published ? "Publicado" : "Borrador"}
              </Badge>
              {isSerializedStatus(product) && <Badge>Serializado</Badge>}
              {product.offers?.some((o) => o.active) && <Badge variant="secondary">Oferta vigente</Badge>}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Imágenes</CardTitle>
          </CardHeader>
          <CardContent>
            {product.images?.length === 0 && (
              <p className="text-sm text-muted-foreground">Sin imágenes.</p>
            )}
            <div className="grid grid-cols-3 gap-2">
              {product.images?.map((img) => (
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

        <Card>
          <CardHeader>
            <CardTitle>Atributos</CardTitle>
          </CardHeader>
          <CardContent>
            {product.attributes?.length === 0 && (
              <p className="text-sm text-muted-foreground">Sin atributos.</p>
            )}
            <div className="flex flex-wrap gap-2">
              {product.attributes?.map((a, i) => (
                <Badge key={i} variant="secondary">
                  {a.attribute}: {a.value}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Seriales</CardTitle>
            {isOwner && product.is_serialized && (
              <Button size="sm" onClick={() => setSerialOpen(true)}>
                <Plus className="mr-1 h-4 w-4" /> Registrar
              </Button>
            )}
          </CardHeader>
          <CardContent>
            {product.serials?.length === 0 && (
              <p className="text-sm text-muted-foreground">Sin seriales registrados.</p>
            )}
            <div className="space-y-2">
              {product.serials?.map((s) => (
                <div key={s.id} className="flex items-center justify-between rounded border p-2 text-sm">
                  <span className="font-mono text-xs">{s.serial_number}</span>
                  <Badge variant={s.status === "AVAILABLE" ? "success" : "secondary"}>
                    {s.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Ofertas</CardTitle>
            {isOwner && product.active && (
              <Button size="sm" onClick={() => setOfferOpen(true)}>
                <Plus className="mr-1 h-4 w-4" /> Nueva oferta
              </Button>
            )}
          </CardHeader>
          <CardContent>
            {product.offers?.length === 0 && (
              <p className="text-sm text-muted-foreground">Sin ofertas.</p>
            )}
            <div className="space-y-2">
              {product.offers?.map((o) => (
                <div key={o.id} className="flex items-center justify-between rounded border p-2 text-sm">
                  <span>
                    S/ {o.normal_price} → <b>S/ {o.offer_price}</b>
                  </span>
                  <Badge variant={o.active ? "default" : "secondary"}>
                    {o.active ? "Vigente" : "Inactiva"}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {serialOpen && (
        <Card>
          <CardContent className="space-y-3 pt-6">
            <h3 className="font-medium">Registrar serial</h3>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1">
                <Label>N.º de serie</Label>
                <Input value={serialNumber} onChange={(e) => setSerialNumber(e.target.value)} />
              </div>
              <div className="space-y-1">
                <Label>IMEI (opcional)</Label>
                <Input value={serialImei} onChange={(e) => setSerialImei(e.target.value)} />
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                disabled={!serialNumber || serialMutation.isPending}
                onClick={() => serialMutation.mutate()}
              >
                Guardar
              </Button>
              <Button variant="ghost" onClick={() => setSerialOpen(false)}>
                Cancelar
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {offerOpen && (
        <Card>
          <CardContent className="space-y-3 pt-6">
            <h3 className="font-medium">Nueva oferta (30 días)</h3>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1">
                <Label>Precio normal</Label>
                <Input type="number" step="0.01" value={normalPrice} onChange={(e) => setNormalPrice(e.target.value)} />
              </div>
              <div className="space-y-1">
                <Label>Precio oferta</Label>
                <Input type="number" step="0.01" value={offerPrice} onChange={(e) => setOfferPrice(e.target.value)} />
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                disabled={!normalPrice || !offerPrice || offerMutation.isPending}
                onClick={() => offerMutation.mutate()}
              >
                Crear oferta
              </Button>
              <Button variant="ghost" onClick={() => setOfferOpen(false)}>
                Cancelar
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {forbidden && (
        <p className="text-sm text-destructive">No tienes permisos para estas acciones.</p>
      )}
    </div>
    </RequireSection>
  );
}

function isSerializedStatus(p: { is_serialized: boolean }): boolean {
  return p.is_serialized;
}