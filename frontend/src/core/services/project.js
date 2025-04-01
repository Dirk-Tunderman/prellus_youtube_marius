import api, { apiRequest } from "./api";

// Helper function to log API requests and responses
const logApiOperation = (operation, url, data = null) => {
  console.log(`[projectService] ${operation} - URL: ${url}`);
  if (data) {
    console.log(`[projectService] ${operation} - Response:`, data);
  }
};

export const projectService = {
  /**
   * Get all projects
   */
  getAllProjects: () => {
    console.log("[projectService] Getting all projects...");
    return apiRequest(async () => {
      const response = await api.get("/projects");
      logApiOperation("getAllProjects", "/projects", response.data);
      return response;
    });
  },

  /**
   * Get transcript text for a project
   * @param {string} projectId - The ID of the project
   */
  getTranscript: (projectId) => {
    console.log(
      `[projectService] Getting transcript for project: ${projectId}`
    );
    return apiRequest(async () => {
      const response = await api.get(`/projects/${projectId}/transcript`);
      logApiOperation(
        "getTranscript",
        `/projects/${projectId}/transcript`,
        response.data
      );
      return response;
    });
  },

  /**
   * Download transcript file
   * @param {string} projectId - The ID of the project
   */
  downloadTranscript: (projectId) => {
    // Create download link and trigger it
    const downloadUrl = `${api.defaults.baseURL}/projects/${projectId}/transcript/download`;
    window.open(downloadUrl, "_blank");
  },

  /**
   * Download audio file
   * @param {string} projectId - The ID of the project
   * @param {string} filename - The name of the audio file
   */
  downloadAudio: (projectId, filename) => {
    // Create download link and trigger it
    const downloadUrl = `${api.defaults.baseURL}/projects/${projectId}/audio/${filename}`;
    window.open(downloadUrl, "_blank");
  },

  /**
   * Delete a project
   * @param {string} projectId - The ID of the project to delete
   */
  deleteProject: (projectId) => {
    console.log(`[projectService] Deleting project: ${projectId}`);
    const url = `/projects/${projectId}`;
    console.log(`[projectService] Delete URL: ${api.defaults.baseURL}${url}`);
    return apiRequest(async () => {
      try {
        const response = await api.delete(url);
        logApiOperation("deleteProject", url, response.data);
        return response;
      } catch (error) {
        console.error(`[projectService] Delete error:`, error);
        throw error;
      }
    });
  },
};
