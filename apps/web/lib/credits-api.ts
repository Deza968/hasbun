import { api } from "./api";
import type {
  CreditAgreement,
  CreditAgreementList,
  CustomerOptionList,
  DelinquencyResponse,
  InstallmentList,
  ValidationResponse,
} from "./types";

export const AGREEMENT_STATUS_LABELS: Record<string, string> = {
  PENDING_APPROVAL: "Pendiente de aprobación",
  APPROVED: "Aprobado",
  ACTIVE: "Activo",
  PAID: "Pagado",
  OVERDUE: "Con mora",
  DEFAULTED: "En mora grave",
  CANCELLED: "Cancelado",
  RESTRUCTURED: "Reestructurado",
};

export const AGREEMENT_STATUS_BADGE: Record<
  string,
  "secondary" | "success" | "destructive" | "outline"
> = {
  PENDING_APPROVAL: "secondary",
  APPROVED: "outline",
  ACTIVE: "success",
  PAID: "outline",
  OVERDUE: "destructive",
  DEFAULTED: "destructive",
  CANCELLED: "secondary",
  RESTRUCTURED: "secondary",
};

export const INSTALLMENT_STATUS_LABELS: Record<string, string> = {
  PENDING: "Pendiente",
  PARTIALLY_PAID: "Pago parcial",
  PAID: "Pagada",
  OVERDUE: "Vencida",
  RESTRUCTURED: "Reprogramada",
  CANCELLED: "Anulada",
};

export const PAYMENT_METHODS = [
  { value: "CASH", label: "Efectivo" },
  { value: "YAPE", label: "Yape" },
  { value: "PLIN", label: "Plin" },
  { value: "CARD", label: "Tarjeta" },
  { value: "BANK_TRANSFER", label: "Transferencia" },
  { value: "OTHER", label: "Otro" },
];

export async function fetchCredits(params: {
  status?: string;
  customer_id?: string;
  search?: string;
  page?: number;
  per_page?: number;
}): Promise<CreditAgreementList> {
  const { data } = await api.get<CreditAgreementList>("/credits", { params });
  return data;
}

export async function fetchCredit(id: string): Promise<CreditAgreement> {
  const { data } = await api.get<CreditAgreement>(`/credits/${id}`);
  return data;
}

export async function fetchCreditInstallments(
  id: string
): Promise<InstallmentList> {
  const { data } = await api.get<InstallmentList>(
    `/credits/${id}/installments`
  );
  return data;
}

export async function fetchInstallments(params: {
  status?: string;
  customer_id?: string;
  due_before?: string;
  page?: number;
  per_page?: number;
}): Promise<InstallmentList> {
  const { data } = await api.get<InstallmentList>("/installments", { params });
  return data;
}

export async function validateCredit(payload: {
  customer_id: string;
  total_amount: string;
  initial_payment: string;
  number_of_installments: number;
}): Promise<ValidationResponse> {
  const { data } = await api.post<ValidationResponse>(
    "/credits/validate",
    payload
  );
  return data;
}

export async function createCredit(payload: Record<string, unknown>): Promise<CreditAgreement> {
  const { data } = await api.post<CreditAgreement>("/credits", payload);
  return data;
}

export async function payInstallment(
  id: string,
  payload: { amount: string; method: string; reference?: string }
): Promise<unknown> {
  const { data } = await api.post(`/installments/${id}/pay`, payload);
  return data;
}

export async function payMultiple(
  agreementId: string,
  payload: { installment_ids: string[]; amount: string; method: string }
): Promise<{ applied_total: string; payments: unknown[] }> {
  const { data } = await api.post(`/credits/${agreementId}/pay-multiple`, payload);
  return data;
}

export async function restructureInstallment(
  id: string,
  payload: { new_due_date: string; reason: string }
): Promise<unknown> {
  const { data } = await api.put(`/installments/${id}/restructure`, payload);
  return data;
}

export async function deliverCredit(id: string): Promise<CreditAgreement> {
  const { data } = await api.post<CreditAgreement>(`/credits/${id}/deliver`);
  return data;
}

export async function fetchDelinquency(): Promise<DelinquencyResponse> {
  const { data } = await api.get<DelinquencyResponse>("/credits/delinquency");
  return data;
}

export async function fetchMyCredits(): Promise<CreditAgreement[]> {
  const { data } = await api.get<CreditAgreement[]>("/credits/my");
  return data;
}

export async function searchCustomers(params: {
  per_page?: number;
}): Promise<CustomerOptionList> {
  const { data } = await api.get<CustomerOptionList>("/customers", { params });
  return data;
}
