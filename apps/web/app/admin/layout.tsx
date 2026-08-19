export default function AdminLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="flex min-h-screen">
      <aside className="w-64 border-r bg-muted/40">Sidebar admin</aside>
      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}