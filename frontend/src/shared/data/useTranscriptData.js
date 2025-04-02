import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { transcriptService } from "@/core/services";
import { toast } from "sonner";

/**
 * Hook for transcript data operations
 * Provides functionality for fetching and processing transcripts
 */
export function useTranscriptData() {
  const queryClient = useQueryClient();

  // Query for fetching all transcripts
  const {
    data: transcripts,
    isLoading: isLoadingTranscripts,
    error: transcriptsError,
  } = useQuery({
    queryKey: ["transcripts"],
    queryFn: async () => {
      return await transcriptService.getTranscripts();
    },
  });

  // Mutation for processing a transcript
  const processTranscript = useMutation({
    mutationFn: async (data) => {
      return await transcriptService.processTranscript(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries(["transcripts"]);
      toast.success("Transcript processed successfully");
    },
    onError: (error) => {
      toast.error(`Error: ${error.message || "Failed to process transcript"}`);
    },
  });

  // Mutation for processing with a specific model
  const processWithModel = useMutation({
    mutationFn: async (data) => {
      return await transcriptService.processWithModel(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries(["transcripts"]);
      toast.success("Transcript processed successfully with selected model");
    },
    onError: (error) => {
      toast.error(
        `Error: ${
          error.message || "Failed to process transcript with selected model"
        }`
      );
    },
  });

  return {
    // Data
    transcripts,
    isLoadingTranscripts,
    transcriptsError,

    // Operations
    processTranscript: processTranscript.mutate,
    processWithModel: processWithModel.mutate,

    // Operation states
    isProcessing: processTranscript.isPending,
    isProcessingWithModel: processWithModel.isPending,
  };
}
