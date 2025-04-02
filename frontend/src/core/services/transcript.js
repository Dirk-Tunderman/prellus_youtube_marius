import api, { apiRequest } from "./api";

export const transcriptService = {
  /**
   * Process a YouTube video to extract transcript
   */
  processTranscript: (data) => {
    console.log("Sending data to API:", data);
    return apiRequest(() => api.post("/transcripts/process", data));
  },

  /**
   * Fetch a list of processed transcripts
   */
  getTranscripts: () => {
    return apiRequest(() => api.get("/transcripts"));
  },

  /**
   * Process a YouTube video with a specific model
   */
  processWithModel: (data) => {
    console.log("Processing with specific model:", data);
    return apiRequest(() => api.post("/transcripts/process/model", data));
  },
};
