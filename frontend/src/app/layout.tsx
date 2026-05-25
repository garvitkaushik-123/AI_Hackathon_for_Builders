import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Link from "next/link";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "CloudOPT - AWS Cost Optimizer",
  description: "AI-powered cloud cost optimization",
};

const navItems = [
  { href: "/", label: "Dashboard", icon: "📊" },
  { href: "/resources", label: "Resources", icon: "🖥️" },
  { href: "/ask", label: "AI Assistant", icon: "🤖" },
  { href: "/settings", label: "Settings", icon: "⚙️" },
];

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} dark h-full antialiased`}
    >
      <body className="bg-gray-950 text-gray-100 min-h-screen flex">
        <aside className="w-64 bg-gray-900 border-r border-gray-800 p-6 flex flex-col">
          <h1 className="text-xl font-bold text-white mb-8">
            <span className="text-emerald-400">Cloud</span>OPT
          </h1>
          <nav className="flex flex-col gap-1">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            ))}
          </nav>
        </aside>
        <main className="flex-1 p-8 overflow-auto">{children}</main>
      </body>
    </html>
  );
}
