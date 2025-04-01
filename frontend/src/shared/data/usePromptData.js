import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { promptService } from "@/core/services";
import { toast } from "sonner";

/**
 * Hook for prompt data operations
 * Provides functionality for managing prompt templates
 */
export function usePromptData() {
  const queryClient = useQueryClient();

  // Query for fetching all prompts
  const {
    data: prompts,
    isLoading: isLoadingPrompts,
    error: promptsError,
  } = useQuery({
    queryKey: ["prompts"],
    queryFn: async () => {
      return await promptService.getAllPrompts();
    },
  });

  // Function to get a specific prompt by ID - direct API call instead of a hook
  const getPrompt = async (promptId) => {
    console.log("Getting prompt with ID:", promptId);
    try {
      const result = await promptService.getPrompt(promptId);
      console.log("Prompt data received:", result);
      return result;
    } catch (error) {
      console.error("Error fetching prompt:", error);
      throw error;
    }
  };

  // Mutation for saving a prompt
  const savePrompt = useMutation({
    mutationFn: async (data) => {
      return await promptService.savePrompt(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries(["prompts"]);
      toast.success("Prompt saved successfully");
    },
    onError: (error) => {
      toast.error(`Error: ${error.message || "Failed to save prompt"}`);
    },
  });

  // Mutation for deleting a prompt
  const deletePrompt = useMutation({
    mutationFn: async (promptId) => {
      return await promptService.deletePrompt(promptId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries(["prompts"]);
      toast.success("Prompt deleted successfully");
    },
    onError: (error) => {
      toast.error(`Error: ${error.message || "Failed to delete prompt"}`);
    },
  });

  return {
    // Data
    prompts,
    isLoadingPrompts,
    promptsError,

    // Operations
    getPrompt,
    savePrompt: savePrompt.mutate,
    deletePrompt: deletePrompt.mutate,

    // Operation states
    isSaving: savePrompt.isPending,
    isDeleting: deletePrompt.isPending,
  };
}
