import { PublicHeader } from "@/components/public-header";

export default function PublicLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <main className="min-h-screen">
      <PublicHeader />
      {children}
    </main>
  );
}