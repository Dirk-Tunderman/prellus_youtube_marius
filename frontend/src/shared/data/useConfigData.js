import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { configService } from "@/core/services";
import { toast } from "sonner";

/**
 * Hook for configuration data operations
 * Provides functionality for managing API keys and model configuration
 */
export function useConfigData() {
  const queryClient = useQueryClient();

  // Query for fetching API keys
  const {
    data: apiKeys,
    isLoading: isLoadingApiKeys,
    error: apiKeysError,
  } = useQuery({
    queryKey: ["config", "apiKeys"],
    queryFn: async () => {
      return await configService.getApiKeys();
    },
  });

  // Query for fetching default model
  const {
    data: defaultModel,
    isLoading: isLoadingDefaultModel,
    error: defaultModelError,
  } = useQuery({
    queryKey: ["config", "defaultModel"],
    queryFn: async () => {
      return await configService.getDefaultModel();
    },
  });

  // Query for fetching available models
  const {
    data: availableModels,
    isLoading: isLoadingAvailableModels,
    error: availableModelsError,
  } = useQuery({
    queryKey: ["config", "availableModels"],
    queryFn: async () => {
      return await configService.getAvailableModels();
    },
  });

  // Mutation for saving an API key
  const saveApiKey = useMutation({
    mutationFn: async (data) => {
      return await configService.saveApiKey(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries(["config", "apiKeys"]);
      queryClient.invalidateQueries(["config", "availableModels"]);
      toast.success("API key saved successfully");
    },
    onError: (error) => {
      toast.error(`Error: ${error.message || "Failed to save API key"}`);
    },
  });

  // Mutation for deleting an API key
  const deleteApiKey = useMutation({
    mutationFn: async (provider) => {
      return await configService.deleteApiKey(provider);
    },
    onSuccess: () => {
      queryClient.invalidateQueries(["config", "apiKeys"]);
      queryClient.invalidateQueries(["config", "availableModels"]);
      toast.success("API key deleted successfully");
    },
    onError: (error) => {
      toast.error(`Error: ${error.message || "Failed to delete API key"}`);
    },
  });

  // Mutation for saving default model
  const saveDefaultModel = useMutation({
    mutationFn: async (data) => {
      return await configService.saveDefaultModel(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries(["config", "defaultModel"]);
      toast.success("Default model saved successfully");
    },
    onError: (error) => {
      toast.error(`Error: ${error.message || "Failed to save default model"}`);
    },
  });

  return {
    // Data
    apiKeys,
    defaultModel,
    availableModels,

    // Loading states
    isLoadingApiKeys,
    isLoadingDefaultModel,
    isLoadingAvailableModels,

    // Error states
    apiKeysError,
    defaultModelError,
    availableModelsError,

    // Operations
    saveApiKey: saveApiKey.mutate,
    deleteApiKey: deleteApiKey.mutate,
    saveDefaultModel: saveDefaultModel.mutate,

    // Operation states
    isSavingApiKey: saveApiKey.isPending,
    isDeletingApiKey: deleteApiKey.isPending,
    isSavingDefaultModel: saveDefaultModel.isPending,
  };
}
