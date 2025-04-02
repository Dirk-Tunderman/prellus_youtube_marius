import { useProjectContext } from "../context/ProjectContext";
import { ProjectCard } from "./ProjectCard";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";
import { useEffect } from "react";

export function ProjectList() {
  const { projects, isLoadingProjects, showTranscript, projectsError } =
    useProjectContext();

  // Debug log when component renders or projects change
  useEffect(() => {
    console.log("[ProjectList] Rendering with projects:", projects);
    console.log("[ProjectList] Loading state:", isLoadingProjects);
    console.log("[ProjectList] Error state:", projectsError);
  }, [projects, isLoadingProjects, projectsError]);

  if (isLoadingProjects) {
    return null; // Loading state is handled by the parent component
  }

  console.log("[ProjectList] Current projects state:", projects);

  if (!projects || projects.length === 0) {
    console.log("[ProjectList] No projects found or empty array");
    return (
      <Alert className="bg-muted">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          No projects found. Start by processing a YouTube video on the Process
          Video page.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div
      className={`grid gap-4 ${
        showTranscript ? "" : "grid-cols-1 md:grid-cols-2 lg:grid-cols-3"
      }`}
    >
      {projects.map((project) => (
        <ProjectCard key={project.id} project={project} />
      ))}
    </div>
  );
}
