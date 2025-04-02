import api, { apiRequest } from "./api";

export const promptService = {
  /**
   * Save a prompt to storage
   * @param {Object} data - Contains promptData and promptName
   */
  savePrompt: (data) => {
    console.log("Saving prompt:", data);
    return apiRequest(() => api.post("/prompts/save", data));
  },
  
  /**
   * Get all saved prompts
   */
  getAllPrompts: () => {
    return apiRequest(() => api.get("/prompts"));
  },
  
  /**
   * Get a specific prompt by ID
   * @param {string} promptId - The unique identifier of the prompt
   */
  getPrompt: (promptId) => {
    return apiRequest(() => api.get(`/prompts/${promptId}`));
  },
  
  /**
   * Delete a specific prompt by ID
   * @param {string} promptId - The unique identifier of the prompt to delete
   */
  deletePrompt: (promptId) => {
    return apiRequest(() => api.delete(`/prompts/${promptId}`));
  },
};
