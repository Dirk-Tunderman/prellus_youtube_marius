import { useState, useEffect } from "react";
import { ProjectList } from "./ProjectList";
import { TranscriptViewer } from "./TranscriptViewer";
import { DeleteConfirmDialog } from "./DeleteConfirmDialog";
import { ProjectProvider, useProjectContext } from "../context/ProjectContext";
import { Skeleton } from "@/components/ui/skeleton";

// Inner component that uses the context
function DownloadsPageContent() {
  const {
    showTranscript,
    showDeleteConfirm,
    isLoadingProjects,
    projects,
    projectToDelete,
  } = useProjectContext();

  // Debug log when showDeleteConfirm or projectToDelete changes
  useEffect(() => {
    console.log("[DownloadsPage] showDeleteConfirm:", showDeleteConfirm);
    console.log("[DownloadsPage] projectToDelete:", projectToDelete);
  }, [showDeleteConfirm, projectToDelete]);

  return (
    <div className="container mx-auto py-6">
      {isLoadingProjects ? (
        <div className="space-y-4">
          <Skeleton className="h-[200px] w-full rounded-lg" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <Skeleton className="h-[150px] w-full rounded-lg" />
            <Skeleton className="h-[150px] w-full rounded-lg" />
            <Skeleton className="h-[150px] w-full rounded-lg" />
          </div>
        </div>
      ) : (
        <div
          className={
            showTranscript ? "grid grid-cols-1 lg:grid-cols-3 gap-6" : ""
          }
        >
          <div className={showTranscript ? "lg:col-span-1" : ""}>
            {showTranscript && (
              <div className="mb-6 lg:mb-0">
                <h2 className="text-xl font-semibold mb-4">Projects</h2>
              </div>
            )}
            <ProjectList />
          </div>

          {showTranscript && (
            <div className="lg:col-span-2">
              <TranscriptViewer />
            </div>
          )}
        </div>
      )}

      {showDeleteConfirm && <DeleteConfirmDialog />}
    </div>
  );
}

// Wrapper component that provides the context
export function DownloadsPage() {
  return (
    <ProjectProvider>
      <DownloadsPageContent />
    </ProjectProvider>
  );
}
