"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
export default function General(){ const q=useQuery({queryKey:["cash-general"],queryFn:async()=>(await api.get("/cash/sessions")).data}); return <div><h1>Caja general</h1><pre>{JSON.stringify(q.data,null,2)}</pre></div>;}
