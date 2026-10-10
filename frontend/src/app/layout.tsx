// @ts-ignore
import type { Metadata } from "next";
import "./globals.css";
import "./pro.css";

export const metadata: Metadata = {
  title: "Satquery AI Pro — Earth Intelligence Workspace",
  description:
    "Explore Earth imagery, compare changes, and inspect agent reasoning in a focused geospatial workspace. Built on BHUVISION by Team BANKAI.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark h-full bg-[#0A0F1C] text-gray-100 antialiased">
      <body className="min-h-full flex flex-col selection:bg-blue-500/30 selection:text-blue-200">
        {children}
      </body>
    </html>
  );
}
