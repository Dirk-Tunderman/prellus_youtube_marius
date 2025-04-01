import { useState, useMemo } from "react";
import { useConfigData } from "@/shared/data/useConfigData";

/**
 * Management hook for configuration settings
 * Builds on shared data hooks to add feature-specific business logic
 */
export function useConfigManagement() {
  // Feature-specific state
  const [newApiKey, setNewApiKey] = useState({ provider: "", key: "" });
  const [selectedProvider, setSelectedProvider] = useState(null);
  const [selectedModel, setSelectedModel] = useState(null);

  // Use the shared data hook
  const {
    apiKeys,
    defaultModel,
    availableModels,
    saveApiKey,
    deleteApiKey,
    saveDefaultModel,
    isSavingApiKey,
    isDeletingApiKey,
    isSavingDefaultModel,
    isLoadingApiKeys,
    isLoadingDefaultModel,
    isLoadingAvailableModels,
  } = useConfigData();

  // Available providers
  const availableProviders = [
    { id: "gemini", name: "Google Gemini" },
    { id: "anthropic", name: "Anthropic Claude" },
  ];

  // Model options with provider grouping
  const modelOptions = useMemo(
    () => [
      // Gemini Models
      {
        value: "gemini-2.5-pro-exp-03-25",
        label: "Google Gemini 2.5 Pro Exp",
        provider: "gemini",
      },
      {
        value: "gemini-2.0-flash",
        label: "Google Gemini 2.0 Flash",
        provider: "gemini",
      },
      {
        value: "gemini-2.0-flash-lite",
        label: "Google Gemini 2.0 Flash Lite",
        provider: "gemini",
      },

      // Anthropic Models
      {
        value: "claude-3-7-sonnet-20250219",
        label: "Anthropic Claude 3.7 Sonnet",
        provider: "anthropic",
      },
      {
        value: "claude-3-5-sonnet-20241022",
        label: "Anthropic Claude 3.5 Sonnet",
        provider: "anthropic",
      },
      {
        value: "claude-3-5-haiku-20241022",
        label: "Anthropic Claude 3.5 Haiku",
        provider: "anthropic",
      },
    ],
    []
  );

  // Check if a provider has an API key configured
  const isProviderConfigured = (providerId) => {
    // Handle the case where apiKeys is an object with provider names as keys
    if (apiKeys && typeof apiKeys === "object" && !Array.isArray(apiKeys)) {
      const isConfigured = !!apiKeys[providerId];
      return isConfigured;
    }

    // Fallback to the original array check for backward compatibility
    if (Array.isArray(apiKeys)) {
      const hasProvider = apiKeys.some((key) => key.provider === providerId);
      return hasProvider;
    }

    return false;
  };

  // Get models for a specific provider
  const getModelsForProvider = (providerId) => {
    return modelOptions.filter((model) => model.provider === providerId);
  };

  // Get recommended models (ones that have API keys configured)
  const getRecommendedModels = () => {
    return modelOptions.filter((model) => isProviderConfigured(model.provider));
  };

  // Check if the selected model's provider is configured
  const isSelectedModelProviderConfigured = () => {
    if (!selectedModel) return false;

    const modelInfo = modelOptions.find(
      (model) => model.value === selectedModel
    );
    if (!modelInfo) return false;

    return isProviderConfigured(modelInfo.provider);
  };

  // Handle API key input change
  const handleApiKeyChange = (provider, key) => {
    setNewApiKey({ provider, key });
  };

  // Save API key
  const handleSaveApiKey = (provider) => {
    if (!newApiKey.key || newApiKey.key.trim() === "") {
      return {
        success: false,
        error: `Please enter a valid ${provider.toUpperCase()} API key`,
      };
    }

    saveApiKey({
      provider,
      key: newApiKey.key,
    });

    // Clear the input field for security
    setNewApiKey({ provider: "", key: "" });
    return { success: true, error: null };
  };

  // Delete API key
  const handleDeleteApiKey = (provider) => {
    deleteApiKey(provider);
    return { success: true, error: null };
  };

  // Save default model
  const handleSaveDefaultModel = () => {
    if (!selectedModel) {
      return { success: false, error: "Please select a model" };
    }

    if (!isSelectedModelProviderConfigured()) {
      return {
        success: false,
        error: "Please configure the API key for this model's provider first",
      };
    }

    saveDefaultModel({ model: selectedModel });
    return { success: true, error: null };
  };

  return {
    // Data from shared hook
    apiKeys,
    defaultModel,
    availableModels,

    // Feature-specific state
    newApiKey,
    selectedProvider,
    setSelectedProvider,
    selectedModel,
    setSelectedModel,

    // Feature-specific data
    availableProviders,
    modelOptions,

    // Feature-specific operations
    isProviderConfigured,
    getModelsForProvider,
    getRecommendedModels,
    isSelectedModelProviderConfigured,
    handleApiKeyChange,
    handleSaveApiKey,
    handleDeleteApiKey,
    handleSaveDefaultModel,

    // Loading states
    isLoadingApiKeys,
    isLoadingDefaultModel,
    isLoadingAvailableModels,

    // Operation states
    isSavingApiKey,
    isDeletingApiKey,
    isSavingDefaultModel,
  };
}
