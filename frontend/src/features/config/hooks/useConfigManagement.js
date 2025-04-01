import { useState, useMemo } from "react";
import { useConfigData } from "@/shared/data/useConfigData";
import { providers, models, getModelsByProvider } from "@/core/registry/models";

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

  // Available providers from the registry
  const availableProviders = providers;

  // Model options from the registry
  const modelOptions = useMemo(() => models, []);

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
    return getModelsByProvider(providerId);
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
