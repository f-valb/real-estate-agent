import type { Metadata } from "next";
import "./globals.css";
import Nav from "@/components/Nav";
import Providers from "./providers";

export const metadata: Metadata = {
  title: "Real Estate Agent",
  description: "AI-powered real estate platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="flex min-h-screen text-gray-900 antialiased">
        <Nav />
        <Providers>
          <main className="flex-1 overflow-auto">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
