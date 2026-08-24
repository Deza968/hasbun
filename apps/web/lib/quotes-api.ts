import { api } from "./api";
import type {
  CustomerOptionList,
  Product,
  ProductList,
  Quote,
  QuoteList,
} from "./types";

export const QUOTE_STATUS_LABELS: Record<string, string> = {
  DRAFT: "Borrador",
  SENT: "Enviada",
  VIEWED: "Vista",
  ACCEPTED: "Aceptada",
  REJECTED: "Rechazada",
  EXPIRED: "Expirada",
  CONVERTED: "Convertida en venta",
};

export const QUOTE_STATUS_BADGE: Record<
  string,
  "secondary" | "success" | "destructive" | "outline"
> = {
  DRAFT: "secondary",
  SENT: "outline",
  VIEWED: "outline",
  ACCEPTED: "success",
  REJECTED: "destructive",
  EXPIRED: "secondary",
  CONVERTED: "success",
};

export async function fetchQuotes(params: {
  status?: string;
  search?: string;
  page?: number;
  per_page?: number;
}): Promise<QuoteList> {
  const { data } = await api.get<QuoteList>("/quotes", { params });
  return data;
}

export async function fetchQuote(id: string): Promise<Quote> {
  const { data } = await api.get<Quote>(`/quotes/${id}`);
  return data;
}

export interface QuoteItemInput {
  product_id: string;
  quantity: string;
  unit_price?: string;
  discount_amount?: string;
}

export async function createQuote(payload: {
  customer_id: string;
  items: QuoteItemInput[];
  valid_until: string;
  notes?: string;
}): Promise<Quote> {
  const { data } = await api.post<Quote>("/quotes", payload);
  return data;
}

export async function updateQuote(
  id: string,
  payload: { valid_until?: string; notes?: string }
): Promise<Quote> {
  const { data } = await api.put<Quote>(`/quotes/${id}`, payload);
  return data;
}

export async function sendQuote(id: string): Promise<Quote> {
  const { data } = await api.post<Quote>(`/quotes/${id}/send`);
  return data;
}

export async function acceptQuote(id: string): Promise<Quote> {
  const { data } = await api.post<Quote>(`/quotes/${id}/accept`);
  return data;
}

export async function rejectQuote(
  id: string,
  reason?: string
): Promise<Quote> {
  const { data } = await api.post<Quote>(`/quotes/${id}/reject`, { reason });
  return data;
}

export async function convertQuote(
  id: string,
  payload: {
    sale_type: "CASH" | "CREDIT";
    cash_session_id?: string;
    initial_payment?: string;
    number_of_installments?: number;
    interest_free_months?: number;
  }
): Promise<{ sale_id: string; sale_code: string; sale_status: string; sale_total: string }> {
  const { data } = await api.post(`/quotes/${id}/convert`, payload);
  return data;
}

export async function searchCustomersForQuote(): Promise<CustomerOptionList> {
  const { data } = await api.get<CustomerOptionList>("/customers", {
    params: { per_page: 100 },
  });
  return data;
}

export async function searchProductsForQuote(params?: {
  search?: string;
}): Promise<ProductList> {
  const { data } = await api.get<ProductList>("/products", {
    params: { per_page: 100, ...params },
  });
  return data;
}

export type { Quote, QuoteList, Product };
