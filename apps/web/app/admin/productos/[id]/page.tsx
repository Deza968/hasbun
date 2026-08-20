"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Plus, Pencil, Trash2 } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useAuth } from "@/hooks/use-auth";
import {
  createOffer,
  deactivateOffer,
  deactivateProduct,
  fetchOffers,
  fetchProduct,
  fetchSerials,
  publishProduct,
  registerSerial,
  unpublishProduct,
  updateSerialStatus,
} from "@/lib/catalog-api";
import { getErrorMessage } from "@/lib/api";
import { formatPrice } from "@/lib/catalog-utils";
import type { SerialUnitStatus } from "@/lib/types";

const SERIAL_STATUS_LABELS: Record<SerialUnitStatus, string> = {
  AVAILABLE: "Disponible",
  RESERVED: "Reservado",
  PARTIALLY_PAID: "Pagado parcial",
  DELIVERED_ON_CREDIT: "Entregado a crédito",
  SOLD: "Vendido",
  IN_REPAIR: "En reparación",
  RETURNED: "Devuelto",
  DAMAGED: "Dañado",
};

export default function ProductoDetallePage({
  params,
}: {
  params: { id: string };
}) {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const isOwner = user?.is_superuser === true;
  const [tab, setTab] = useState<"general" | "serials" | "offers">("general");
  const [error, setError] = useState<string | null>(null);

  // Oferta
  const [normalPrice, setNormalPrice] = useState("");
  const [offerPrice, setOfferPrice] = useState("");
  const [startAt, setStartAt] = useState("");
  const [endAt, setEndAt] = useState("");

  // Serial
  const [serialNumber, setSerialNumber] = useState("");
  const [imei, setImei] = useState("");

  const productQuery = useQuery({
    queryKey: ["products", params.id],
    queryFn: () => fetchProduct(params.id),
  });
  const serialsQuery = useQuery({
    queryKey: ["serials", params.id],
    queryFn: () => fetchSerials(params.id),
    enabled: tab === "serials",
  });
  const offersQuery = useQuery({
    queryKey: ["offers", params.id],
    queryFn: () => fetchOffers(params.id),
    enabled: tab === "offers",
  });

  const product = productQuery.data;

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ["products", params.id] });
    void queryClient.invalidateQueries({ queryKey: ["serials", params.id] });
    void queryClient.invalidateQueries({ queryKey: ["offers", params.id] });
  };

  const publishMutation = useMutation({
    mutationFn: () => {
      if (!product) return Promise.reject(new Error("Producto no cargado"));
      return product.published
        ? unpublishProduct(product.id)
        : publishProduct(product.id);
    },
    onSuccess: invalidate,
    onError: (e) => setError(getErrorMessage(e)),
  });
  const deactivateMutation = useMutation({
    mutationFn: () => deactivateProduct(params.id),
    onSuccess: invalidate,
    onError: (e) => setError(getErrorMessage(e)),
  });
  const offerMutation = useMutation({
    mutationFn: () =>
      createOffer(params.id, {
        normal_price: Number(normalPrice),
        offer_price: Number(offerPrice),
        start_at: new Date(startAt).toISOString(),
        end_at: new Date(endAt).toISOString(),
      }),
    onSuccess: () => {
      setNormalPrice("");
      setOfferPrice("");
      setStartAt("");
      setEndAt("");
      void queryClient.invalidateQueries({ queryKey: ["offers", params.id] });
      invalidate();
    },
    onError: (e) => setError(getErrorMessage(e)),
  });
  const deactivateOfferMutation = useMutation({
    mutationFn: (offerId: string) => deactivateOffer(params.id, offerId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["offers", params.id] });
      invalidate();
    },
    onError: (e) => setError(getErrorMessage(e)),
  });
  const serialMutation = useMutation({
    mutationFn: () =>
      registerSerial(params.id, {
        serial_number: serialNumber,
        imei: imei || null,
      }),
    onSuccess: () => {
      setSerialNumber("");
      setImei("");
      void queryClient.invalidateQueries({ queryKey: ["serials", params.id] });
      invalidate();
    },
    onError: (e) => setError(getErrorMessage(e)),
  });
  const statusMutation = useMutation({
    mutationFn: ({ serialId, status }: { serialId: string; status: SerialUnitStatus }) =>
      updateSerialStatus(params.id, serialId, status),
    onSuccess: () =>
      void queryClient.invalidateQueries({ queryKey: ["serials", params.id] }),
    onError: (e) => setError(getErrorMessage(e)),
  });

  if (productQuery.isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!product) {
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
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold">{product.name}</h1>
            <Badge variant={product.active ? "success" : "destructive"}>
              {product.active ? "Activo" : "Inactivo"}
            </Badge>
            <Badge variant={product.published ? "default" : "secondary"}>
              {product.published ? "Publicado" : "Borrador"}
            </Badge>
          </div>
          <p className="font-mono text-sm text-muted-foreground">
            SKU {product.sku}
          </p>
        </div>
        <div className="flex gap-2">
          {isOwner && (
            <>
              <Button
                variant="outline"
                onClick={() => publishMutation.mutate()}
              >
                {product.published ? "Despublicar" : "Publicar"}
              </Button>
              <Button asChild>
                <Link href={`/admin/productos/${product.id}/editar`}>
                  <Pencil className="mr-2 h-4 w-4" />
                  Editar
                </Link>
              </Button>
              {product.active && (
                <Button
                  variant="destructive"
                  onClick={() => deactivateMutation.mutate()}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Desactivar
                </Button>
              )}
            </>
          )}
        </div>
      </div>

      {error && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      <div className="flex gap-1 rounded-md border p-1">
        {(
          [
            ["general", "General"],
            ["serials", "Seriales"],
            ["offers", "Ofertas"],
          ] as const
        ).map(([value, label]) => (
          <button
            key={value}
            onClick={() => setTab(value)}
            className={`flex-1 rounded-md px-3 py-2 text-sm ${
              tab === value ? "bg-primary text-primary-foreground" : "hover:bg-accent"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "general" && (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Información</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="grid grid-cols-2">
                <span className="text-muted-foreground">Marca</span>
                <span>{product.brand_name ?? "—"}</span>
              </div>
              <div className="grid grid-cols-2">
                <span className="text-muted-foreground">Categoría</span>
                <span>{product.category_name ?? "—"}</span>
              </div>
              <div className="grid grid-cols-2">
                <span className="text-muted-foreground">Moneda</span>
                <span>{product.currency}</span>
              </div>
              <div className="grid grid-cols-2">
                <span className="text-muted-foreground">Regla de precio</span>
                <span>{product.price_rule}</span>
              </div>
              <div className="grid grid-cols-2">
                <span className="text-muted-foreground">Serializado</span>
                <span>{product.is_serialized ? "Sí" : "No"}</span>
              </div>
              <div className="grid grid-cols-2">
                <span className="text-muted-foreground">Stock mínimo</span>
                <span>{product.stock_minimum}</span>
              </div>
              <div className="grid grid-cols-2">
                <span className="text-muted-foreground">Peso</span>
                <span>{product.weight_kg ? `${product.weight_kg} kg` : "—"}</span>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Precios</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="grid grid-cols-2">
                <span className="text-muted-foreground">Costo</span>
                <span>{formatPrice(product.cost_price)}</span>
              </div>
              <div className="grid grid-cols-2">
                <span className="text-muted-foreground">Precio de venta</span>
                <span>{formatPrice(product.sale_price)}</span>
              </div>
              <div className="grid grid-cols-2">
                <span className="text-muted-foreground">Precio vigente</span>
                <span className="font-semibold">
                  {formatPrice(product.current_price)}
                </span>
              </div>
              {product.active_offer && (
                <p className="rounded bg-emerald-50 px-2 py-1 text-emerald-700">
                  Oferta activa hasta{" "}
                  {new Date(product.active_offer.end_at).toLocaleDateString()}
                </p>
              )}
            </CardContent>
          </Card>
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Atributos</CardTitle>
            </CardHeader>
            <CardContent>
              {product.attributes.length === 0 ? (
                <p className="text-sm text-muted-foreground">Sin atributos.</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {product.attributes.map((attr) => (
                    <Badge key={attr.value_id} variant="secondary">
                      {attr.attribute_name}: {attr.value}
                    </Badge>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {tab === "serials" && (
        <div className="space-y-4">
          {product.is_serialized && (
            <Card>
              <CardHeader>
                <CardTitle>Registrar serial</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-wrap items-end gap-3">
                <div className="space-y-1">
                  <Label>Número de serie *</Label>
                  <Input
                    value={serialNumber}
                    onChange={(e) => setSerialNumber(e.target.value)}
                  />
                </div>
                <div className="space-y-1">
                  <Label>IMEI</Label>
                  <Input value={imei} onChange={(e) => setImei(e.target.value)} />
                </div>
                <Button
                  onClick={() => serialMutation.mutate()}
                  disabled={!serialNumber}
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Registrar
                </Button>
              </CardContent>
            </Card>
          )}
          <Card>
            <CardContent className="p-0">
              {serialsQuery.isLoading ? (
                <div className="flex justify-center py-10">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Serial</TableHead>
                      <TableHead>IMEI</TableHead>
                      <TableHead>Estado</TableHead>
                      {isOwner && <TableHead className="text-right">Acción</TableHead>}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(serialsQuery.data ?? []).length === 0 ? (
                      <TableRow>
                        <TableCell
                          colSpan={isOwner ? 4 : 3}
                          className="py-8 text-center text-sm text-muted-foreground"
                        >
                          Sin seriales registrados
                        </TableCell>
                      </TableRow>
                    ) : (
                      (serialsQuery.data ?? []).map((serial) => (
                        <TableRow key={serial.id}>
                          <TableCell className="font-mono text-xs">
                            {serial.serial_number}
                          </TableCell>
                          <TableCell>{serial.imei ?? "—"}</TableCell>
                          <TableCell>
                            <Badge variant="secondary">
                              {SERIAL_STATUS_LABELS[serial.status]}
                            </Badge>
                          </TableCell>
                          {isOwner && (
                            <TableCell className="text-right">
                              <Select
                                className="h-8 w-44"
                                value={serial.status}
                                onChange={(e) =>
                                  statusMutation.mutate({
                                    serialId: serial.id,
                                    status: e.target.value as SerialUnitStatus,
                                  })
                                }
                              >
                                {Object.entries(SERIAL_STATUS_LABELS).map(
                                  ([value, label]) => (
                                    <option key={value} value={value}>
                                      {label}
                                    </option>
                                  )
                                )}
                              </Select>
                            </TableCell>
                          )}
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {tab === "offers" && (
        <div className="space-y-4">
          {isOwner && (
            <Card>
              <CardHeader>
                <CardTitle>Nueva oferta</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-3 md:grid-cols-5">
                <div className="space-y-1">
                  <Label>Precio normal</Label>
                  <Input
                    type="number"
                    value={normalPrice}
                    onChange={(e) => setNormalPrice(e.target.value)}
                  />
                </div>
                <div className="space-y-1">
                  <Label>Precio oferta</Label>
                  <Input
                    type="number"
                    value={offerPrice}
                    onChange={(e) => setOfferPrice(e.target.value)}
                  />
                </div>
                <div className="space-y-1">
                  <Label>Inicio</Label>
                  <Input
                    type="date"
                    value={startAt}
                    onChange={(e) => setStartAt(e.target.value)}
                  />
                </div>
                <div className="space-y-1">
                  <Label>Fin</Label>
                  <Input
                    type="date"
                    value={endAt}
                    onChange={(e) => setEndAt(e.target.value)}
                  />
                </div>
                <Button
                  className="self-end"
                  disabled={!normalPrice || !offerPrice || !startAt || !endAt}
                  onClick={() => offerMutation.mutate()}
                >
                  Crear oferta
                </Button>
              </CardContent>
            </Card>
          )}
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Normal</TableHead>
                    <TableHead>Oferta</TableHead>
                    <TableHead>Vigencia</TableHead>
                    <TableHead>Estado</TableHead>
                    {isOwner && <TableHead className="text-right">Acción</TableHead>}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(offersQuery.data ?? []).length === 0 ? (
                    <TableRow>
                      <TableCell
                        colSpan={isOwner ? 5 : 4}
                        className="py-8 text-center text-sm text-muted-foreground"
                      >
                        Sin ofertas
                      </TableCell>
                    </TableRow>
                  ) : (
                    (offersQuery.data ?? []).map((offer) => {
                      const active =
                        offer.active &&
                        new Date(offer.start_at) <= new Date() &&
                        new Date(offer.end_at) >= new Date();
                      return (
                        <TableRow key={offer.id}>
                          <TableCell>{formatPrice(offer.normal_price)}</TableCell>
                          <TableCell className="font-semibold text-emerald-600">
                            {formatPrice(offer.offer_price)}
                          </TableCell>
                          <TableCell className="text-sm">
                            {new Date(offer.start_at).toLocaleDateString()} —{" "}
                            {new Date(offer.end_at).toLocaleDateString()}
                          </TableCell>
                          <TableCell>
                            <Badge variant={active ? "success" : "secondary"}>
                              {active ? "Activa" : "Inactiva"}
                            </Badge>
                          </TableCell>
                          {isOwner && (
                            <TableCell className="text-right">
                              <Button
                                variant="ghost"
                                size="sm"
                                disabled={!offer.active}
                                onClick={() =>
                                  deactivateOfferMutation.mutate(offer.id)
                                }
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </TableCell>
                          )}
                        </TableRow>
                      );
                    })
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}