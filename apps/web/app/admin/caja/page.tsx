"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { useState } from "react";

export default function CajaPage() {
  const qc = useQueryClient();
  const [amount, setAmount] = useState("100");
  const [counted, setCounted] = useState("");
  const active = useQuery({ queryKey: ["cash-active"], queryFn: async () => (await api.get("/cash/sessions/active")).data });
  const openMut = useMutation({ mutationFn: async () => (await api.post("/cash/sessions/open", { register_id: active.data?.register_id ?? undefined, opening_amount: amount })).data, onSuccess: () => qc.invalidateQueries({ queryKey: ["cash-active"] }) });
  const closeMut = useMutation({ mutationFn: async () => (await api.post(`/cash/sessions/${active.data.id}/close`, { counted_cash: counted })).data, onSuccess: () => qc.invalidateQueries({ queryKey: ["cash-active"] }) });
  if (active.isLoading) return <p>Cargando...</p>;
  const session = active.data;
  if (!session) return <Card><CardContent className="p-6"><p>No hay sesión abierta</p><div className="flex gap-2 mt-2"><Input value={amount} onChange={e=>setAmount(e.target.value)} placeholder="Monto inicial"/><Button onClick={()=>openMut.mutate()}>Abrir caja</Button></div></CardContent></Card>;
  return <Card><CardContent className="p-6 space-y-3"><p>Sesión {session.id} - {session.status}</p><p>Balance esperado: {session.expected_cash ?? "-"}</p><div className="flex gap-2"><Input value={counted} onChange={e=>setCounted(e.target.value)} placeholder="Efectivo contado"/><Button onClick={()=>closeMut.mutate()}>Cerrar caja</Button></div></CardContent></Card>;
}
