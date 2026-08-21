import type { Metadata } from "next";
import { Providers } from "@/components/providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "Inversiones Hasbun - Tecnología y Servicios",
  description:
    "Venta de tecnología, electrodomésticos, reparaciones, instalaciones y personalización en Sicuani, Cusco, Perú.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}