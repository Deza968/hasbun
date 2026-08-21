"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function ClientesPage() {
  const q = useQuery({ queryKey: ["customers"], queryFn: async () => (await api.get("/customers")).data });
  return <div><div className="flex justify-between mb-4"><h1 className="text-xl font-semibold">Clientes</h1><Link href="/admin/clientes/nuevo"><Button>Nuevo</Button></Link></div><Table><TableHeader><TableRow><TableHead>Nombre</TableHead><TableHead>DNI/RUC</TableHead><TableHead>Teléfono</TableHead></TableRow></TableHeader><TableBody>{(q.data?.items??[]).map((c:any)=><TableRow key={c.id}><TableCell>{c.first_name} {c.last_name} {c.razon_social}</TableCell><TableCell>{c.dni||c.ruc}</TableCell><TableCell>{c.phone}</TableCell></TableRow>)}</TableBody></Table></div>;
}
