import { Link, useLocation } from "react-router-dom";

export function Navbar() {
  const location = useLocation();

  const isActive = (path) => {
    return (
      location.pathname === path ||
      (path !== "/" && location.pathname.startsWith(path))
    );
  };

  return (
    <header className="bg-primary text-primary-foreground">
      <div className="container mx-auto py-4 px-4">
        <div className="flex justify-between items-center">
          <div className="font-bold text-xl">YouTube Transcript Processor</div>

          <nav className="flex gap-6">
            <Link
              to="/"
              className={`transition-colors hover:text-primary-foreground/80 ${
                isActive("/") && !isActive("/config") && !isActive("/downloads")
                  ? "font-bold"
                  : "text-primary-foreground/70"
              }`}
            >
              Process Video
            </Link>

            <Link
              to="/config"
              className={`transition-colors hover:text-primary-foreground/80 ${
                isActive("/config") ? "font-bold" : "text-primary-foreground/70"
              }`}
            >
              Configuration
            </Link>

            <Link
              to="/downloads"
              className={`transition-colors hover:text-primary-foreground/80 ${
                isActive("/downloads")
                  ? "font-bold"
                  : "text-primary-foreground/70"
              }`}
            >
              Downloads
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
}
