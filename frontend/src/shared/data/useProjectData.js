import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { projectService } from "@/core/services";
import { toast } from "sonner";
import { useEffect } from "react";

/**
 * Hook for project data operations
 * Provides functionality for managing projects and downloads
 */
export function useProjectData() {
  const queryClient = useQueryClient();

  // Query for fetching all projects
  const {
    data: projects,
    isLoading: isLoadingProjects,
    error: projectsError,
  } = useQuery({
    queryKey: ["projects"],
    queryFn: async () => {
      const result = await projectService.getAllProjects();
      return result;
    },
  });

  // Function to get a transcript for a specific project

  // Function to get a transcript for a specific project
  const getTranscript = (projectId) => {
    return useQuery({
      queryKey: ["projects", projectId, "transcript"],
      queryFn: async () => {
        return await projectService.getTranscript(projectId);
      },
      enabled: !!projectId, // Only run if projectId is provided
    });
  };

  // Function for downloading transcript (no need for React Query)
  const downloadTranscript = (projectId) => {
    projectService.downloadTranscript(projectId);
  };

  // Function for downloading audio (no need for React Query)
  const downloadAudio = (projectId, filename) => {
    projectService.downloadAudio(projectId, filename);
  };

  // Mutation for deleting a project
  const deleteProject = useMutation({
    mutationFn: async (projectId) => {
      return await projectService.deleteProject(projectId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries(["projects"]);
      toast.success("Project deleted successfully");
    },
    onError: (error) => {
      toast.error(`Error: ${error.message || "Failed to delete project"}`);
    },
  });

  return {
    // Data
    projects,
    isLoadingProjects,
    projectsError,

    // Operations
    getTranscript,
    downloadTranscript,
    downloadAudio,
    deleteProject: deleteProject.mutate,

    // Operation states
    isDeleting: deleteProject.isPending,
  };
}
