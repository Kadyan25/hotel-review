import { Outlet } from "react-router-dom";
import { BackgroundDecoration } from "./BackgroundDecoration";
import { Header } from "./Header";

export function Layout() {
  return (
    <div className="min-h-screen">
      <BackgroundDecoration />
      <Header />
      <main className="mx-auto max-w-6xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}
