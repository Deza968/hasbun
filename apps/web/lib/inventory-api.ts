import { api } from "./api";
import type {
  Kardex,
  Purchase,
  PurchaseList,
  StockList,
  Supplier,
  SupplierList,
} from "./types";

export async function fetchStock(params: {
  search?: string;
  low?: boolean;
  page?: number;
  per_page?: number;
}): Promise<StockList> {
  const { data } = await api.get<StockList>("/inventory/stock", { params });
  return data;
}

export async function fetchKardex(
  productId: string,
  params?: {
    date_from?: string;
    date_to?: string;
    movement_type?: string;
    page?: number;
    per_page?: number;
  }
): Promise<Kardex> {
  const { data } = await api.get<Kardex>(`/inventory/kardex/${productId}`, {
    params,
  });
  return data;
}

export async function createAdjustment(payload: {
  product_id: string;
  quantity: string;
  reason: string;
  notes?: string | null;
}): Promise<unknown> {
  const { data } = await api.post("/inventory/adjustments", payload);
  return data;
}

export async function fetchSuppliers(params: {
  search?: string;
  active?: boolean;
  page?: number;
  per_page?: number;
}): Promise<SupplierList> {
  const { data } = await api.get<SupplierList>("/suppliers", { params });
  return data;
}

export async function fetchSupplier(id: string): Promise<Supplier> {
  const { data } = await api.get<Supplier>(`/suppliers/${id}`);
  return data;
}

export async function createSupplier(
  payload: Partial<Supplier>
): Promise<Supplier> {
  const { data } = await api.post<Supplier>("/suppliers", payload);
  return data;
}

export async function updateSupplier(
  id: string,
  payload: Partial<Supplier>
): Promise<Supplier> {
  const { data } = await api.put<Supplier>(`/suppliers/${id}`, payload);
  return data;
}

export async function deactivateSupplier(id: string): Promise<Supplier> {
  const { data } = await api.delete<Supplier>(`/suppliers/${id}`);
  return data;
}

export async function fetchPurchases(params: {
  supplier_id?: string;
  status?: string;
  page?: number;
  per_page?: number;
}): Promise<PurchaseList> {
  const { data } = await api.get<PurchaseList>("/purchases", { params });
  return data;
}

export async function fetchPurchase(id: string): Promise<Purchase> {
  const { data } = await api.get<Purchase>(`/purchases/${id}`);
  return data;
}

export interface PurchaseCreatePayload {
  supplier_id: string;
  currency: string;
  exchange_rate: string;
  exchange_rate_source?: string | null;
  notes?: string | null;
  items: {
    product_id: string;
    quantity: string;
    unit_cost: string;
    notes?: string | null;
  }[];
}

export async function createPurchase(
  payload: PurchaseCreatePayload
): Promise<Purchase> {
  const { data } = await api.post<Purchase>("/purchases", payload);
  return data;
}

export async function confirmPurchase(id: string): Promise<Purchase> {
  const { data } = await api.post<Purchase>(`/purchases/${id}/confirm`);
  return data;
}

export async function receivePurchase(
  id: string,
  received_items: { item_id: string; received_quantity: string }[]
): Promise<Purchase> {
  const { data } = await api.post<Purchase>(`/purchases/${id}/receive`, {
    received_items,
  });
  return data;
}

export async function cancelPurchase(
  id: string,
  reason: string
): Promise<Purchase> {
  const { data } = await api.post<Purchase>(`/purchases/${id}/cancel`, {
    reason,
  });
  return data;
}