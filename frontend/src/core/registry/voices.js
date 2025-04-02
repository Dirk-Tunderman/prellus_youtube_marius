/**
 * Voice Registry
 *
 * This file serves as the central registry for all voice options used in the application.
 * It follows the Configuration Registry pattern to centralize voice definitions.
 *
 * IMPORTANT: To add, remove, or modify voices, you only need to update this file.
 * All components will automatically use the updated information.
 *
 * HOW TO USE:
 *
 * 1. Getting all voices:
 *    - Use getAllVoices() to get a flat array of all voice options
 *
 * 2. Getting voices by accent:
 *    - Use getVoicesByAccent('american') or getVoicesByAccent('british')
 *
 * 3. Finding a specific voice:
 *    - Use getVoiceByValue('af_bella') to find a specific voice by its value
 */

// Voice definitions grouped by accent
export const voices = {
  // American English voices
  american: [
    { value: "af_heart", label: "Heart (Female)" },
    { value: "af_alloy", label: "Alloy (Female)" },
    { value: "af_aoede", label: "Aoede (Female)" },
    { value: "af_bella", label: "Bella (Female)" },
    { value: "af_jessica", label: "Jessica (Female)" },
    { value: "af_kore", label: "Kore (Female)" },
    { value: "af_nicole", label: "Nicole (Female)" },
    { value: "af_nova", label: "Nova (Female)" },
    { value: "af_river", label: "River (Female)" },
    { value: "af_sarah", label: "Sarah (Female)" },
    { value: "af_sky", label: "Sky (Female)" },
    { value: "am_adam", label: "Adam (Male)" },
    { value: "am_echo", label: "Echo (Male)" },
    { value: "am_eric", label: "Eric (Male)" },
    { value: "am_fenrir", label: "Fenrir (Male)" },
    { value: "am_liam", label: "Liam (Male)" },
    { value: "am_michael", label: "Michael (Male)" },
    { value: "am_onyx", label: "Onyx (Male)" },
    { value: "am_puck", label: "Puck (Male)" },
    { value: "am_santa", label: "Santa (Male)" },
  ],

  // British English voices
  british: [
    { value: "bf_alice", label: "Alice (Female)" },
    { value: "bf_emma", label: "Emma (Female)" },
    { value: "bf_isabella", label: "Isabella (Female)" },
    { value: "bf_lily", label: "Lily (Female)" },
    { value: "bm_daniel", label: "Daniel (Male)" },
    { value: "bm_fable", label: "Fable (Male)" },
    { value: "bm_george", label: "George (Male)" },
    { value: "bm_lewis", label: "Lewis (Male)" },
  ],
};

/**
 * Get all voices as a flat array
 * @returns {Array} Array of all voice objects
 */
export const getAllVoices = () => {
  return [...voices.american, ...voices.british];
};

/**
 * Get voices by accent
 * @param {string} accent - The accent ('american' or 'british')
 * @returns {Array} Array of voice objects for the specified accent
 */
export const getVoicesByAccent = (accent) => {
  return voices[accent] || [];
};

/**
 * Get a voice by its value
 * @param {string} value - The voice value
 * @returns {Object|undefined} The voice object or undefined if not found
 */
export const getVoiceByValue = (value) => {
  return getAllVoices().find((voice) => voice.value === value);
};
