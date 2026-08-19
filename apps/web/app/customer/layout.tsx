export default function CustomerLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="flex min-h-screen">
      <aside className="w-64 border-r bg-muted/40">Panel cliente</aside>
      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}