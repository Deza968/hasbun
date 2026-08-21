"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
export default function Solicitudes(){ const q=useQuery({queryKey:["closures"],queryFn:async()=>(await api.get("/cash/closure-requests")).data}); return <div><h1>Solicitudes cierre</h1><pre>{JSON.stringify(q.data,null,2)}</pre></div>;}
