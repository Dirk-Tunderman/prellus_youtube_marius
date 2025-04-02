import { createContext, useContext, useState, useEffect } from "react";
import { useProjectData } from "@/shared/data/useProjectData";
import { formatDate } from "@/lib/utils";

// Create context
const ProjectContext = createContext(null);

// Context provider component
export function ProjectProvider({ children }) {
  // Feature-specific state
  const [selectedProjectId, setSelectedProjectId] = useState(null);
  const [showTranscript, setShowTranscript] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState(null);

  // Use the shared data hook
  const {
    projects,
    getTranscript,
    downloadTranscript,
    downloadAudio,
    deleteProject,
    isLoadingProjects,
    isDeleting,
    projectsError,
  } = useProjectData();

  // Debug log when projects data changes
  useEffect(() => {
    console.log("[ProjectContext] Projects data:", projects);
    console.log("[ProjectContext] Error state:", projectsError);
  }, [projects, projectsError]);

  // Debug effect to monitor state changes
  useEffect(() => {
    console.log(
      "[ProjectContext] State changed - showDeleteConfirm:",
      showDeleteConfirm
    );
    console.log(
      "[ProjectContext] State changed - projectToDelete:",
      projectToDelete
    );
  }, [showDeleteConfirm, projectToDelete]);

  // Get selected project
  const selectedProject = projects?.find((p) => p.id === selectedProjectId);

  // Get transcript for selected project
  const { data: transcript, isLoading: isLoadingTranscript } = getTranscript(
    selectedProjectId || ""
  );

  // Format YouTube URL for display
  const formatYoutubeUrl = (url) => {
    if (!url) return "";

    // If URL is very long, truncate it for display
    if (url.length > 50) {
      return url.substring(0, 47) + "...";
    }
    return url;
  };

  // Get display name for the project
  const getProjectDisplayName = (project) => {
    // If project has a title, use it; otherwise use the ID
    return project.name || project.id.split("_")[0];
  };

  // View transcript
  const handleViewTranscript = (project) => {
    setSelectedProjectId(project.id);
    setShowTranscript(true);
  };

  // Handle transcript download
  const handleDownloadTranscript = () => {
    if (selectedProjectId) {
      downloadTranscript(selectedProjectId);
    }
  };

  // Handle audio download
  const handleDownloadAudio = (projectId, filename) => {
    downloadAudio(projectId, filename);
  };

  // Copy transcript to clipboard
  const copyTranscript = () => {
    if (!transcript?.text)
      return { success: false, error: "No transcript content available" };

    try {
      navigator.clipboard.writeText(transcript.text);
      return { success: true, error: null };
    } catch (err) {
      console.error("Could not copy text: ", err);
      return { success: false, error: "Failed to copy transcript" };
    }
  };

  // Show delete confirmation
  const confirmDelete = (project) => {
    console.log("[ProjectContext] confirmDelete called with project:", project);

    // Use a single state update to ensure consistency
    setProjectToDelete(project);
    setShowDeleteConfirm(true);

    console.log("[ProjectContext] State updates requested");
  };

  // Handle project deletion
  const handleDeleteProject = () => {
    if (!projectToDelete)
      return { success: false, error: "No project selected for deletion" };

    deleteProject(projectToDelete.id);

    // If the deleted project is currently shown in transcript view, go back to list
    if (selectedProjectId === projectToDelete.id) {
      setShowTranscript(false);
    }

    setShowDeleteConfirm(false);
    setProjectToDelete(null);
    return { success: true, error: null };
  };

  // Cancel delete
  const cancelDelete = () => {
    setShowDeleteConfirm(false);
    setProjectToDelete(null);
  };

  // Create context value
  const contextValue = {
    // Data from shared hook
    projects,
    projectsError,

    // Feature-specific state
    selectedProjectId,
    setSelectedProjectId,
    selectedProject,
    showTranscript,
    setShowTranscript,
    showDeleteConfirm,
    projectToDelete,

    // Derived data
    transcript,

    // Helper functions
    formatDate,
    formatYoutubeUrl,
    getProjectDisplayName,

    // Feature-specific operations
    handleViewTranscript,
    handleDownloadTranscript,
    handleDownloadAudio,
    copyTranscript,
    confirmDelete,
    handleDeleteProject,
    cancelDelete,

    // Loading states
    isLoadingProjects,
    isLoadingTranscript,

    // Operation states
    isDeleting,
  };

  return (
    <ProjectContext.Provider value={contextValue}>
      {children}
    </ProjectContext.Provider>
  );
}

// Custom hook to use the context
export function useProjectContext() {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error("useProjectContext must be used within a ProjectProvider");
  }
  return context;
}
