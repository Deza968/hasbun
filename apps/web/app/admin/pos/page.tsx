"use client";
import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";

export default function POSPage() {
  const [search, setSearch] = useState("");
  const [cart, setCart] = useState<any[]>([]);
  const products = useQuery({ queryKey: ["pos-products", search], queryFn: async () => (await api.get("/products", { params: { search, per_page: 10, published: true } })).data, enabled: search.length>1 });
  const saleMut = useMutation({ mutationFn: async () => (await api.post("/sales", { items: cart.map(c=>({ product_id: c.id, quantity: c.qty })), payments: [{ method: "CASH", amount: cart.reduce((s,c)=>s+c.price*c.qty,0) }], cash_session_id: undefined })).data, onSuccess: ()=>setCart([]) });
  return <div className="grid grid-cols-2 gap-4"><Card><CardContent className="p-4"><Input autoFocus placeholder="Buscar por SKU/nombre" value={search} onChange={e=>setSearch(e.target.value)}/>{products.data?.items?.map((p:any)=><div key={p.id} className="flex justify-between py-1"><span>{p.name} - S/ {p.sale_price}</span><Button size="sm" onClick={()=>setCart([...cart,{id:p.id,name:p.name,price:Number(p.sale_price),qty:1}])}>Agregar</Button></div>)}</CardContent></Card><Card><CardContent className="p-4"><p>Carrito ({cart.length})</p>{cart.map((c,i)=><div key={i} className="flex justify-between"><span>{c.name} x{c.qty}</span><span>S/ {(c.price*c.qty).toFixed(2)}</span></div>)}<p className="font-bold">Total S/ {cart.reduce((s,c)=>s+c.price*c.qty,0).toFixed(2)}</p><Button className="w-full mt-2" onClick={()=>saleMut.mutate()}>Cobrar</Button></CardContent></Card></div>;
}
