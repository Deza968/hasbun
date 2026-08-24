"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, CheckCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  fetchNotifications,
  fetchUnreadCount,
  markAllNotificationsRead,
  markNotificationRead,
} from "@/lib/whatsapp-api";

export function NotificationsBell() {
  const [open, setOpen] = React.useState(false);
  const queryClient = useQueryClient();

  const unread = useQuery({
    queryKey: ["notifications-unread"],
    queryFn: fetchUnreadCount,
    refetchInterval: 30_000,
  });

  const list = useQuery({
    queryKey: ["notifications"],
    queryFn: () => fetchNotifications({ per_page: 10 }),
    enabled: open,
  });

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ["notifications"] });
    void queryClient.invalidateQueries({ queryKey: ["notifications-unread"] });
  };

  const markRead = useMutation({
    mutationFn: markNotificationRead,
    onSuccess: invalidate,
  });
  const markAll = useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: invalidate,
  });

  const count = unread.data?.unread ?? 0;

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="icon"
        aria-label="Notificaciones"
        onClick={() => setOpen((o) => !o)}
      >
        <Bell className="h-5 w-5" />
        {count > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-semibold text-white">
            {count > 9 ? "9+" : count}
          </span>
        )}
      </Button>

      {open && (
        <div className="absolute right-0 top-10 z-50 w-96 rounded-md border bg-background shadow-lg">
          <div className="flex items-center justify-between border-b px-3 py-2">
            <p className="text-sm font-medium">Notificaciones</p>
            <Button
              variant="ghost"
              size="sm"
              disabled={markAll.isPending || count === 0}
              onClick={() => markAll.mutate()}
            >
              <CheckCheck className="mr-1 h-3 w-3" /> Marcar todas
            </Button>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {(list.data?.items ?? []).length === 0 && (
              <p className="px-3 py-6 text-center text-sm text-muted-foreground">
                Sin notificaciones
              </p>
            )}
            {(list.data?.items ?? []).map((n) => (
              <button
                key={n.id}
                type="button"
                onClick={() => {
                  if (!n.read) markRead.mutate(n.id);
                }}
                className={cn(
                  "block w-full border-b px-3 py-2 text-left hover:bg-accent",
                  !n.read && "bg-primary/5"
                )}
              >
                <div className="flex items-center gap-2">
                  <p className="flex-1 truncate text-sm font-medium">
                    {n.title}
                  </p>
                  <Badge
                    variant={
                      n.priority === "URGENT" || n.priority === "HIGH"
                        ? "destructive"
                        : "secondary"
                    }
                    className="text-[10px]"
                  >
                    {n.priority}
                  </Badge>
                </div>
                <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">
                  {n.message}
                </p>
                <p className="mt-1 text-[10px] text-muted-foreground">
                  {new Date(n.created_at).toLocaleString("es-PE")}
                </p>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
