"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import Link from "next/link";

export default function VentasPage() {
  const q = useQuery({ queryKey: ["sales"], queryFn: async () => (await api.get("/sales")).data });
  return <div><h1 className="text-xl font-semibold mb-4">Ventas</h1><Table><TableHeader><TableRow><TableHead>Código</TableHead><TableHead>Estado</TableHead><TableHead>Total</TableHead><TableHead>Acciones</TableHead></TableRow></TableHeader><TableBody>{(q.data?.items??[]).map((s:any)=><TableRow key={s.id}><TableCell>{s.code}</TableCell><TableCell>{s.status}</TableCell><TableCell>S/ {s.total}</TableCell><TableCell><Link href={`/admin/ventas/${s.id}`}>Ver</Link></TableCell></TableRow>)}</TableBody></Table></div>;
}
