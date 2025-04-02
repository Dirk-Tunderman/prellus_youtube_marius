import api, { apiRequest } from "./api";

export const audioService = {
  /**
   * Generate audio from a transcript
   */
  generateAudio: (transcriptId) => {
    return apiRequest(() => api.post(`/audio/generate/${transcriptId}`));
  },
};
