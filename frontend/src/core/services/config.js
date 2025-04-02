import api, { apiRequest } from "./api";

export const configService = {
  /**
   * Get configuration of API keys (which ones are set)
   */
  getApiKeys: () => {
    return apiRequest(() => api.get("/config/apikeys"));
  },

  /**
   * Save an API key for a specific service
   * @param {Object} data - Contains provider and key
   */
  saveApiKey: (data) => {
    return apiRequest(() => api.post("/config/apikeys", data));
  },

  /**
   * Delete an API key for a specific service
   * @param {string} provider - The service provider (openai, gemini, etc.)
   */
  deleteApiKey: (provider) => {
    return apiRequest(() => api.delete(`/config/apikeys/${provider}`));
  },

  /**
   * Get the current default model
   */
  getDefaultModel: () => {
    return apiRequest(() => api.get("/config/defaultmodel"));
  },

  /**
   * Save the default model
   * @param {Object} data - Contains model name
   */
  saveDefaultModel: (data) => {
    return apiRequest(() => api.post("/config/defaultmodel", data));
  },

  /**
   * Get all available models with availability status
   */
  getAvailableModels: () => {
    return apiRequest(() => api.get("/config/models"));
  },
};
