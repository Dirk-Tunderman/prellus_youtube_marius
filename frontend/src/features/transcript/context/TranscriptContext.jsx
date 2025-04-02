import { createContext, useContext, useState, useEffect } from "react";
import { useTranscriptData } from "@/shared/data/useTranscriptData";
import { usePromptData } from "@/shared/data/usePromptData";
import { extractYoutubeId } from "@/lib/utils";

// Create context
const TranscriptContext = createContext(null);

export function TranscriptProvider({ children }) {
  // UI state (persisted between route changes)
  const [showSavePrompt, setShowSavePrompt] = useState(false);
  const [showPromptList, setShowPromptList] = useState(false);

  // Form state now lives directly in the context
  const [formState, setFormState] = useState({
    url: "",
    title: "",
    duration: 30,
    promptName: "",
    voice: "af_bella", // Default to a high-quality American female voice
    speed: 0.7, // Default speed in the middle of the range
    promptData: {
      yourRole: "",
      scriptStructure: "",
      toneAndStyle: "",
      retentionAndFlow: "",
      additionalInstructions: "",
    },
  });

  // Use the shared data hooks (but not for form state)
  const { transcripts, processTranscript, processWithModel, isProcessing } =
    useTranscriptData();

  const { prompts, savePrompt, getPrompt, deletePrompt, isSaving, isDeleting } =
    usePromptData();

  // Extract form state values for convenience
  const url = formState.url || "";
  const title = formState.title || "";
  const duration = formState.duration || "";
  const promptName = formState.promptName || "";
  const voice = formState.voice || "af_bella";
  const speed = formState.speed || 0.7;
  const promptData = formState.promptData || {
    yourRole: "",
    scriptStructure: "",
    toneAndStyle: "",
    retentionAndFlow: "",
    additionalInstructions: "",
  };

  // Wrapper functions to update form state
  const setUrl = (newUrl) => {
    setFormState((prev) => ({ ...prev, url: newUrl }));
  };

  const setTitle = (newTitle) => {
    setFormState((prev) => ({ ...prev, title: newTitle }));
  };

  const setDuration = (newDuration) => {
    setFormState((prev) => ({ ...prev, duration: newDuration }));
  };

  const setPromptName = (newPromptName) => {
    setFormState((prev) => ({ ...prev, promptName: newPromptName }));
  };

  const setVoice = (newVoice) => {
    setFormState((prev) => ({ ...prev, voice: newVoice }));
  };

  const setSpeed = (newSpeed) => {
    setFormState((prev) => ({ ...prev, speed: newSpeed }));
  };

  // Auto-populate title when URL changes
  useEffect(() => {
    if (url) {
      const videoId = extractYoutubeId(url);
      if (videoId && !title) {
        setTitle(`YouTube Transcript - ${videoId}`);
      }
    }
  }, [url, title, setTitle]);

  // Handle changes to prompt fields
  const handlePromptChange = (field, value) => {
    setFormState((prev) => ({
      ...prev,
      promptData: {
        ...prev.promptData,
        [field]: value,
      },
    }));
  };

  // Reset form
  const resetForm = () => {
    setFormState({
      url: "",
      title: "",
      duration: "",
      promptName: "",
      voice: "bm_lewis",
      speed: 0.7,
      promptData: {
        yourRole: "",
        scriptStructure: "",
        toneAndStyle: "",
        retentionAndFlow: "",
        additionalInstructions: "",
      },
    });
  };

  // Validate form
  const validateForm = () => {
    if (!url) {
      return { valid: false, error: "Please enter a YouTube URL" };
    }

    const videoId = extractYoutubeId(url);
    if (!videoId) {
      return { valid: false, error: "Please enter a valid YouTube URL" };
    }

    return { valid: true, error: null };
  };

  // Process transcript
  const handleProcessTranscript = () => {
    const validation = validateForm();
    if (!validation.valid) {
      return { success: false, error: validation.error };
    }

    // Only parse duration if it's not empty
    const durationValue = duration === "" ? undefined : parseInt(duration);

    processTranscript({
      url,
      title,
      promptData,
      duration: durationValue,
      voice,
      speed,
    });

    return { success: true, error: null };
  };

  // Process with specific model
  const handleProcessWithModel = (modelId) => {
    const validation = validateForm();
    if (!validation.valid) {
      return { success: false, error: validation.error };
    }

    // Only parse duration if it's not empty
    const durationValue = duration === "" ? undefined : parseInt(duration);

    processWithModel({
      url,
      title,
      promptData,
      duration: durationValue,
      modelId,
      voice,
      speed,
    });

    return { success: true, error: null };
  };

  // Save prompt template
  const handleSavePrompt = () => {
    if (!promptName.trim()) {
      return { success: false, error: "Please enter a name for your prompt" };
    }

    savePrompt({
      promptData,
      promptName,
    });

    setShowSavePrompt(false);
    return { success: true, error: null };
  };

  // Delete prompt template
  const handleDeletePrompt = (promptId) => {
    deletePrompt(promptId);
    return { success: true, error: null };
  };

  // Load prompt template
  const handleLoadPrompt = async (promptId) => {
    try {
      console.log("Loading prompt with ID:", promptId);
      const data = await getPrompt(promptId);
      console.log("Prompt data received:", data);

      if (data && data.promptData) {
        // The data already has the correct structure, no need to map field names
        setFormState((prev) => ({
          ...prev,
          promptData: data.promptData,
          promptName: data.metaData.prompt_name || "",
        }));
        return { success: true, error: null };
      } else {
        console.error("Invalid prompt data format:", data);
        return { success: false, error: "Failed to load prompt data" };
      }
    } catch (error) {
      console.error("Error loading prompt:", error);
      return { success: false, error: "Failed to load prompt" };
    } finally {
      setShowPromptList(false);
    }
  };

  // Create context value
  const contextValue = {
    // Form state
    url,
    setUrl,
    title,
    setTitle,
    duration,
    setDuration,
    voice,
    setVoice,
    speed,
    setSpeed,
    promptData,
    handlePromptChange,

    // Prompt management
    promptName,
    setPromptName,
    showSavePrompt,
    setShowSavePrompt,
    showPromptList,
    setShowPromptList,
    prompts,

    // Operations
    handleProcessTranscript,
    handleProcessWithModel,
    handleSavePrompt,
    handleLoadPrompt,
    handleDeletePrompt,
    resetForm,
    validateForm,

    // Operation states
    isProcessing,
    isSaving,
    isDeleting,
  };

  return (
    <TranscriptContext.Provider value={contextValue}>
      {children}
    </TranscriptContext.Provider>
  );
}

// Custom hook to use the context
export function useTranscriptContext() {
  const context = useContext(TranscriptContext);
  if (!context) {
    throw new Error(
      "useTranscriptContext must be used within a TranscriptProvider"
    );
  }
  return context;
}
