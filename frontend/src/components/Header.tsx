export function Header() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center gap-3 px-6 py-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 text-sm font-bold text-white">
          A
        </div>
        <div>
          <p className="text-sm font-semibold leading-tight text-slate-900">Azzurro Hotels</p>
          <p className="text-xs leading-tight text-slate-500">Review Insights Dashboard</p>
        </div>
      </div>
    </header>
  );
}
