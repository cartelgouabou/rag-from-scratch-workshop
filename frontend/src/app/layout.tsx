import type { Metadata } from "next";

import { NavigationTabs } from "@/components/NavigationTabs";
import { ThemeProvider } from "@/components/ThemeProvider";
import { ThemeToggle } from "@/components/ThemeToggle";

import "./globals.css";

export const metadata: Metadata = {
  title: "RAG Workshop",
  description: "Assistant personnel RAG multi-source avec routage SQL / VECTOR / BOTH.",
};

const themeScript = `
try {
  const t = localStorage.getItem('theme');
  if (t === 'light') document.documentElement.classList.remove('dark');
  else document.documentElement.classList.add('dark');
} catch (_) {}
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr" className="dark" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>
        <ThemeProvider>
          <div className="mx-auto min-h-screen max-w-7xl px-6 py-8">
            <header className="mb-8 flex flex-col gap-4 rounded-3xl border border-slate-200 bg-white/80 p-6 backdrop-blur md:flex-row md:items-center md:justify-between dark:border-slate-800 dark:bg-slate-950/50">
              <div>
                <p className="text-sm uppercase tracking-[0.3em] text-indigo-600 dark:text-indigo-300">
                  DermaScan Workshop
                </p>
                <h1 className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">
                  RAG multi-source
                </h1>
                <p className="mt-2 max-w-2xl text-sm text-slate-600 dark:text-slate-400">
                  Chargez vos documents, interrogez votre base de connaissance et
                  laissez l&apos;assistant router automatiquement entre SQL, VECTOR et BOTH.
                </p>
              </div>
              <div className="flex items-center gap-3">
                <ThemeToggle />
                <NavigationTabs />
              </div>
            </header>
            {children}
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
