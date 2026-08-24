import { api } from "./api";
import type {
  NotificationList,
  WhatsAppConfig,
  WhatsAppMessage,
  WhatsAppMessageList,
  WhatsAppTemplate,
} from "./types";

export const WHATSAPP_EVENT_LABELS: Record<string, string> = {
  NEW_SALE: "Nueva venta",
  PAYMENT_RECEIVED: "Pago recibido",
  INSTALLMENT_UPCOMING: "Cuota por vencer",
  INSTALLMENT_OVERDUE: "Cuota vencida",
  MORA_CREATED: "Mora generada",
  REPAIR_CREATED: "Reparación ingresada",
  REPAIR_READY: "Reparación lista",
  QUOTE_CREATED: "Cotización enviada",
  QUOTE_ACCEPTED: "Cotización aceptada",
  INSTALLATION_CREATED: "Instalación programada",
  INSTALLATION_UPCOMING: "Instalación próxima",
  STOCK_LOW: "Stock bajo",
  STOCK_OUT: "Sin stock",
  WARRANTY_EXPIRING: "Garantía por vencer",
  SALE_COMPLETED: "Crédito completado",
};

export const MESSAGE_STATUS_LABELS: Record<string, string> = {
  PENDING: "Pendiente",
  SENT: "Enviado",
  DELIVERED: "Entregado",
  FAILED: "Fallido",
};

export async function fetchWhatsAppMessages(params: {
  status?: string;
  page?: number;
  per_page?: number;
}): Promise<WhatsAppMessageList> {
  const { data } = await api.get<WhatsAppMessageList>("/whatsapp/messages", {
    params,
  });
  return data;
}

export async function retryWhatsAppMessage(id: string): Promise<WhatsAppMessage> {
  const { data } = await api.post<WhatsAppMessage>(
    `/whatsapp/messages/${id}/retry`
  );
  return data;
}

export async function fetchWhatsAppTemplates(): Promise<WhatsAppTemplate[]> {
  const { data } = await api.get<WhatsAppTemplate[]>("/whatsapp/templates");
  return data;
}

export async function updateWhatsAppTemplate(
  id: string,
  payload: { body?: string; active?: boolean }
): Promise<WhatsAppTemplate> {
  const { data } = await api.put<WhatsAppTemplate>(
    `/whatsapp/templates/${id}`,
    payload
  );
  return data;
}

export async function fetchWhatsAppConfig(): Promise<WhatsAppConfig> {
  const { data } = await api.get<WhatsAppConfig>("/whatsapp/config");
  return data;
}

export async function updateWhatsAppConfig(
  enabled: boolean
): Promise<WhatsAppConfig> {
  const { data } = await api.put<WhatsAppConfig>("/whatsapp/config", null, {
    params: { enabled },
  });
  return data;
}

// --- Notificaciones internas ---

export async function fetchNotifications(params?: {
  unread_only?: boolean;
  per_page?: number;
}): Promise<NotificationList> {
  const { data } = await api.get<NotificationList>("/notifications", {
    params,
  });
  return data;
}

export async function fetchUnreadCount(): Promise<{ unread: number }> {
  const { data } = await api.get<{ unread: number }>(
    "/notifications/unread-count"
  );
  return data;
}

export async function markNotificationRead(id: string): Promise<unknown> {
  const { data } = await api.post(`/notifications/${id}/read`);
  return data;
}

export async function markAllNotificationsRead(): Promise<unknown> {
  const { data } = await api.post("/notifications/read-all");
  return data;
}
