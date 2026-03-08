import type { Metadata } from "next";
import "./globals.css";
import { ReturnProvider } from "@/context/ReturnContext";
import { AuthProvider } from "@/context/AuthContext";

export const metadata: Metadata = {
  title: "TaxApp — Smart Tax Preparation",
  description:
    "Free federal and state tax preparation for individuals and self-employed filers. Includes audit risk scoring and personalized deduction recommendations.",
  keywords: "tax preparation, 1040, federal taxes, Illinois taxes, Minnesota taxes, self-employed taxes, free tax filing",
  openGraph: {
    title: "TaxApp — Smart Tax Preparation",
    description: "Prepare your federal + state taxes with audit risk scoring and deduction recommendations.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased min-h-screen" style={{ background: "var(--bg-primary)" }}>
        <AuthProvider>
          <ReturnProvider>{children}</ReturnProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
