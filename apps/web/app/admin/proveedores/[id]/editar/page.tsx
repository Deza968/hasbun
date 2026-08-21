"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  createSupplier,
  fetchSupplier,
  updateSupplier,
} from "@/lib/inventory-api";
import { getErrorMessage, isForbidden } from "@/lib/api";
import { RequireSection } from "@/components/guards";

export default function ProveedorFormPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const editing = Boolean(params.id);

  const [form, setForm] = useState({
    razon_social: "",
    ruc: "",
    nombre_comercial: "",
    contacto_nombre: "",
    telefono: "",
    telefono_whatsapp: "",
    email: "",
    direccion: "",
    ciudad: "",
    notes: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);

  const supplierQuery = useQuery({
    queryKey: ["supplier", params.id],
    queryFn: () => fetchSupplier(params.id),
    enabled: editing,
  });

  useEffect(() => {
    const s = supplierQuery.data;
    if (editing && s) {
      setForm({
        razon_social: s.razon_social ?? "",
        ruc: s.ruc ?? "",
        nombre_comercial: s.nombre_comercial ?? "",
        contacto_nombre: s.contacto_nombre ?? "",
        telefono: s.telefono ?? "",
        telefono_whatsapp: s.telefono_whatsapp ?? "",
        email: s.email ?? "",
        direccion: s.direccion ?? "",
        ciudad: s.ciudad ?? "",
        notes: s.notes ?? "",
      });
    }
  }, [editing, supplierQuery.data]);

  useEffect(() => {
    if (isForbidden(supplierQuery.error)) setForbidden(true);
    else if (supplierQuery.error)
      setError(getErrorMessage(supplierQuery.error));
  }, [supplierQuery.error]);

  const saveMutation = useMutation({
    mutationFn: () =>
      editing
        ? updateSupplier(params.id, form)
        : createSupplier(form),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["suppliers"] });
      router.push("/admin/proveedores");
    },
    onError: (e) => {
      if (isForbidden(e)) setForbidden(true);
      setError(getErrorMessage(e));
    },
  });

  const set = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [key]: e.target.value }));

  if (forbidden) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-destructive">
          No tienes permisos para gestionar proveedores.
        </CardContent>
      </Card>
    );
  }

  return (
    <RequireSection section="proveedores">
      <div className="mx-auto max-w-2xl space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">
            {editing ? "Editar proveedor" : "Nuevo proveedor"}
          </h1>
          <Button
            disabled={!form.razon_social.trim() || saveMutation.isPending}
            onClick={() => saveMutation.mutate()}
          >
            {saveMutation.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : null}
            Guardar
          </Button>
        </div>

        {error && (
          <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Información del proveedor</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label>Razón social *</Label>
                <Input value={form.razon_social} onChange={set("razon_social")} />
              </div>
              <div className="space-y-2">
                <Label>RUC</Label>
                <Input value={form.ruc} onChange={set("ruc")} maxLength={11} />
              </div>
              <div className="space-y-2">
                <Label>Nombre comercial</Label>
                <Input value={form.nombre_comercial} onChange={set("nombre_comercial")} />
              </div>
              <div className="space-y-2">
                <Label>Contacto</Label>
                <Input value={form.contacto_nombre} onChange={set("contacto_nombre")} />
              </div>
              <div className="space-y-2">
                <Label>Teléfono</Label>
                <Input value={form.telefono} onChange={set("telefono")} />
              </div>
              <div className="space-y-2">
                <Label>WhatsApp</Label>
                <Input value={form.telefono_whatsapp} onChange={set("telefono_whatsapp")} />
              </div>
              <div className="space-y-2">
                <Label>Email</Label>
                <Input type="email" value={form.email} onChange={set("email")} />
              </div>
              <div className="space-y-2">
                <Label>Ciudad</Label>
                <Input value={form.ciudad} onChange={set("ciudad")} />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Dirección</Label>
              <Input value={form.direccion} onChange={set("direccion")} />
            </div>
            <div className="space-y-2">
              <Label>Notas</Label>
              <textarea
                className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm"
                rows={3}
                value={form.notes}
                onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </RequireSection>
  );
}