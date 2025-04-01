import { Outlet } from "react-router-dom";
import { Navbar } from "./Navbar";
import { Toaster } from "@/components/ui/sonner";
import { TranscriptProvider } from "@/features/transcript/context/TranscriptContext";
import { ProjectProvider } from "@/features/downloads/context/ProjectContext";

export function RootLayout() {
  return (
    <TranscriptProvider>
      <ProjectProvider>
        <div className="min-h-screen bg-background">
          <Navbar />
          <main className="container mx-auto py-6 px-4">
            <Outlet />
          </main>
          <Toaster />
        </div>
      </ProjectProvider>
    </TranscriptProvider>
  );
}
