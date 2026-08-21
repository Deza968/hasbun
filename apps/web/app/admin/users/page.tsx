"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Plus } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  assignRole,
  createUser,
  deactivateUser,
  fetchRoles,
  fetchUsers,
  removeRole,
} from "@/lib/auth-api";
import { getErrorMessage, isForbidden } from "@/lib/api";
import { RequireSection } from "@/components/guards";

export default function UsersPage() {
  const queryClient = useQueryClient();

  const usersQuery = useQuery({ queryKey: ["users"], queryFn: fetchUsers });
  const rolesQuery = useQuery({ queryKey: ["roles"], queryFn: fetchRoles });

  const [createOpen, setCreateOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);

  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [roleCode, setRoleCode] = useState("");

  const invalidate = () =>
    void queryClient.invalidateQueries({ queryKey: ["users"] });

  const createMutation = useMutation({
    mutationFn: () =>
      createUser({
        email,
        username,
        full_name: fullName,
        phone: phone || null,
        password,
        role_codes: roleCode ? [roleCode] : [],
      }),
    onSuccess: () => {
      setCreateOpen(false);
      setError(null);
      setEmail("");
      setUsername("");
      setFullName("");
      setPhone("");
      setPassword("");
      setRoleCode("");
      invalidate();
    },
    onError: (e) => {
      if (isForbidden(e)) setForbidden(true);
      setError(getErrorMessage(e));
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: deactivateUser,
    onSuccess: invalidate,
    onError: (e) => {
      if (isForbidden(e)) setForbidden(true);
      setError(getErrorMessage(e));
    },
  });

  const assignMutation = useMutation({
    mutationFn: ({ userId, roleCode }: { userId: string; roleCode: string }) =>
      assignRole(userId, roleCode),
    onSuccess: invalidate,
    onError: (e) => {
      if (isForbidden(e)) setForbidden(true);
      setError(getErrorMessage(e));
    },
  });

  const removeRoleMutation = useMutation({
    mutationFn: ({ userId, roleCode }: { userId: string; roleCode: string }) =>
      removeRole(userId, roleCode),
    onSuccess: invalidate,
    onError: (e) => {
      if (isForbidden(e)) setForbidden(true);
      setError(getErrorMessage(e));
    },
  });

  if (forbidden) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-destructive">
          No tienes permisos para gestionar usuarios (roles.users o
          users.ver/gestion).
        </CardContent>
      </Card>
    );
  }

  return (
    <RequireSection section="users">
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Usuarios</h1>
          <p className="text-sm text-muted-foreground">
            {usersQuery.data?.total ?? 0} registrados
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Nuevo usuario
        </Button>
      </div>

      {error && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      <Card>
        <CardContent className="p-0">
          {usersQuery.isLoading ? (
            <div className="flex justify-center py-10">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Usuario</TableHead>
                  <TableHead>Correo</TableHead>
                  <TableHead>Roles</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead className="text-right">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(usersQuery.data?.items ?? []).map((user) => (
                  <TableRow key={user.id}>
                    <TableCell className="font-medium">
                      {user.full_name}
                      <span className="block text-xs text-muted-foreground">
                        @{user.username}
                      </span>
                    </TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>
                      <div className="flex flex-wrap items-center gap-1">
                        {user.roles.map((role) => (
                          <Badge key={role} variant="secondary">
                            {role}
                          </Badge>
                        ))}
                        <Select
                          className="h-7 w-28"
                          value=""
                          onChange={(e) =>
                            assignMutation.mutate({
                              userId: user.id,
                              roleCode: e.target.value,
                            })
                          }
                        >
                          <option value="">+ rol</option>
                          {(rolesQuery.data ?? [])
                            .filter((r) => !user.roles.includes(r.code))
                            .map((r) => (
                              <option key={r.code} value={r.code}>
                                {r.name}
                              </option>
                            ))}
                        </Select>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={user.is_active ? "success" : "destructive"}
                      >
                        {user.is_active ? "Activo" : "Inactivo"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        {user.roles.map((role) => (
                          <Button
                            key={role}
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              removeRoleMutation.mutate({
                                userId: user.id,
                                roleCode: role,
                              })
                            }
                          >
                            Quitar {role}
                          </Button>
                        ))}
                        {user.is_active && (
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() =>
                              deactivateMutation.mutate(user.id)
                            }
                          >
                            Desactivar
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nuevo usuario</DialogTitle>
            <DialogDescription>
              La contraseña debe tener al menos 8 caracteres, una mayúscula y
              un número.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Correo</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="username">Nombre de usuario</Label>
              <Input
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="fullName">Nombre completo</Label>
              <Input
                id="fullName"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="phone">Teléfono</Label>
              <Input
                id="phone"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Contraseña</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="role">Rol inicial</Label>
              <Select
                id="role"
                value={roleCode}
                onChange={(e) => setRoleCode(e.target.value)}
              >
                <option value="">Sin rol</option>
                {(rolesQuery.data ?? []).map((r) => (
                  <option key={r.code} value={r.code}>
                    {r.name}
                  </option>
                ))}
              </Select>
            </div>
            <Button
              className="w-full"
              disabled={createMutation.isPending}
              onClick={() => createMutation.mutate()}
            >
              {createMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Crear usuario
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
    </RequireSection>
  );
}