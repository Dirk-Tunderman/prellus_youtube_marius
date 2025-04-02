/**
 * Text-to-Speech utility functions and constants
 */

// Language options
export const languageOptions = [
  { value: "a", label: "American English" },
  { value: "b", label: "British English" },
  { value: "e", label: "Spanish" },
  { value: "f", label: "French" },
  { value: "h", label: "Hindi" },
  { value: "i", label: "Italian" },
  { value: "p", label: "Brazilian Portuguese" },
  { value: "j", label: "Japanese" },
  { value: "z", label: "Mandarin Chinese" },
];

// Voice options grouped by category
export const voiceOptions = {
  americanFemale: [
    { value: "af_bella", label: "Bella" },
    { value: "af_nicole", label: "Nicole" },
    { value: "af_sky", label: "Sky" },
    { value: "af_sarah", label: "Sarah" },
  ],
  americanMale: [
    { value: "am_adam", label: "Adam" },
    { value: "am_michael", label: "Michael" },
  ],
  britishFemale: [
    { value: "bf_emma", label: "Emma" },
    { value: "bf_isabella", label: "Isabella" },
  ],
  britishMale: [
    { value: "bm_george", label: "George" },
    { value: "bm_lewis", label: "Lewis" },
  ],
};

// Get all voices as a flat array
export const getAllVoices = () => {
  return [
    ...voiceOptions.americanFemale,
    ...voiceOptions.americanMale,
    ...voiceOptions.britishFemale,
    ...voiceOptions.britishMale,
  ];
};

// Get voice label by value
export const getVoiceLabel = (voiceValue) => {
  const voice = getAllVoices().find((v) => v.value === voiceValue);
  return voice ? voice.label : voiceValue;
};

// Get language label by value
export const getLanguageLabel = (languageValue) => {
  const language = languageOptions.find((l) => l.value === languageValue);
  return language ? language.label : languageValue;
};

// Default TTS settings
export const defaultTtsSettings = {
  language: "a",
  voice: "af_bella",
  speed: 1.0,
};
