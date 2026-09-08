import type { Metadata } from "next";
import "./globals.css";
import { Footer } from "@/components/layout/footer";
import { Header } from "@/components/layout/header";
import { QueryProvider } from "@/lib/query/query-provider";

export const metadata: Metadata = {
  title: "AlgoVision",
  description: "Interactive algorithm visualizations that make every step clear.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className="dark h-full antialiased"
    >
      <body className="min-h-full bg-background text-foreground"><QueryProvider><div className="flex min-h-screen flex-col"><Header /><main className="flex-1">{children}</main><Footer /></div></QueryProvider></body>
    </html>
  );
}
