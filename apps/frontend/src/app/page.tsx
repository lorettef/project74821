import Link from "next/link";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-zinc-200 px-6 py-4 dark:border-zinc-800">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <span className="text-xl font-bold tracking-tight">Startup Engine</span>
          <nav className="flex items-center gap-4 text-sm">
            <Link
              href="/login"
              className="rounded-lg px-4 py-2 text-zinc-600 transition-colors hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
            >
              Войти
            </Link>
            <Link
              href="/register"
              className="rounded-lg bg-zinc-900 px-4 py-2 text-white transition-colors hover:bg-zinc-800 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-200"
            >
              Регистрация
            </Link>
          </nav>
        </div>
      </header>

      <main className="flex flex-1 items-center justify-center px-6">
        <div className="max-w-3xl text-center">
          <h1 className="text-5xl font-bold leading-tight tracking-tight sm:text-6xl">
            SaaS Analytics Platform
          </h1>
          <p className="mt-6 text-xl leading-relaxed text-zinc-600 dark:text-zinc-400">
            Платформа для управления SaaS-стартапом на всех стадиях роста: от
            идеи до pre-IPO. Трекайте метрики, анализируйте когорты, считайте
            runway и получайте AI-рекомендации.
          </p>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-6 text-sm">
            <div className="rounded-lg border border-zinc-200 px-6 py-4 text-left dark:border-zinc-800">
              <div className="font-semibold">7 стадий</div>
              <div className="mt-1 text-zinc-500">от идеи до series D</div>
            </div>
            <div className="rounded-lg border border-zinc-200 px-6 py-4 text-left dark:border-zinc-800">
              <div className="font-semibold">10+ метрик</div>
              <div className="mt-1 text-zinc-500">MRR, CAC, LTV, Churn</div>
            </div>
            <div className="rounded-lg border border-zinc-200 px-6 py-4 text-left dark:border-zinc-800">
              <div className="font-semibold">AI-аналитика</div>
              <div className="mt-1 text-zinc-500">GigaChat от Сбера</div>
            </div>
          </div>
          <div className="mt-12">
            <Link
              href="/register"
              className="inline-flex h-12 items-center justify-center rounded-lg bg-zinc-900 px-8 text-base font-medium text-white transition-colors hover:bg-zinc-800 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-200"
            >
              Начать бесплатно
            </Link>
          </div>
        </div>
      </main>

      <footer className="border-t border-zinc-200 px-6 py-4 text-center text-sm text-zinc-500 dark:border-zinc-800">
        Startup Engine v2.0
      </footer>
    </div>
  );
}
