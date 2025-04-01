import { useState, useEffect, useMemo } from "react";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { useConfigManagement } from "../hooks";
import { toast } from "sonner";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle, CheckCircle2 } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  getProviderById,
  getUniqueProviderIdsFromModels,
} from "@/core/registry/models";

export function DefaultModelSelector() {
  const {
    defaultModel,
    selectedModel,
    setSelectedModel,
    modelOptions,
    isProviderConfigured,
    isSelectedModelProviderConfigured,
    handleSaveDefaultModel,
    isLoadingDefaultModel,
    isSavingDefaultModel,
    apiKeys,
    availableModels,
  } = useConfigManagement();

  // Debug logs
  useEffect(() => {
    console.log("API Keys:", JSON.stringify(apiKeys, null, 2));
    console.log("Available Models:", JSON.stringify(availableModels, null, 2));
    console.log("Default Model:", JSON.stringify(defaultModel, null, 2));
    console.log("Is Gemini Configured:", isProviderConfigured("gemini"));
    console.log("Model Options:", JSON.stringify(modelOptions, null, 2));
  }, [
    apiKeys,
    availableModels,
    defaultModel,
    isProviderConfigured,
    modelOptions,
  ]);

  const onSaveDefaultModel = () => {
    const result = handleSaveDefaultModel();
    if (!result.success) {
      toast.error(result.error);
      return;
    }

    // Reset the selected model after successfully saving
    setSelectedModel(null);
    toast.success("Default model saved successfully!");
  };

  if (isLoadingDefaultModel) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-32" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label htmlFor="model-select" className="text-sm font-medium">
            Select Model
            {defaultModel && (
              <span className="ml-2 text-sm text-muted-foreground">
                (Current default: {defaultModel?.model})
              </span>
            )}
          </label>
        </div>

        <Select value={selectedModel} onValueChange={setSelectedModel}>
          <SelectTrigger id="model-select" className="w-full">
            <SelectValue placeholder="Select a model" />
          </SelectTrigger>
          <SelectContent>
            {/* Dynamically generate model groups based on providers in the registry */}
            {getUniqueProviderIdsFromModels().map((providerId) => {
              const providerInfo = getProviderById(providerId);
              return (
                <SelectGroup key={providerId}>
                  <SelectLabel>{providerInfo.name} Models</SelectLabel>
                  {modelOptions
                    .filter((model) => model.provider === providerId)
                    .map((model) => (
                      <SelectItem
                        key={model.value}
                        value={model.value}
                        disabled={!isProviderConfigured(providerId)}
                      >
                        {model.label}
                        {!isProviderConfigured(providerId) &&
                          " (API key required)"}
                      </SelectItem>
                    ))}
                </SelectGroup>
              );
            })}
          </SelectContent>
        </Select>
      </div>

      {selectedModel && !isSelectedModelProviderConfigured() && (
        <Alert
          variant="warning"
          className="bg-amber-50 text-amber-800 border-amber-200"
        >
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Please configure the API key for this model's provider first.
          </AlertDescription>
        </Alert>
      )}

      {selectedModel &&
        isSelectedModelProviderConfigured() &&
        defaultModel?.model === selectedModel && (
          <Alert
            variant="success"
            className="bg-green-50 text-green-800 border-green-200"
          >
            <CheckCircle2 className="h-4 w-4" />
            <AlertDescription>
              This model is already set as the default.
            </AlertDescription>
          </Alert>
        )}

      <Button
        onClick={onSaveDefaultModel}
        disabled={
          !selectedModel ||
          !isSelectedModelProviderConfigured() ||
          isSavingDefaultModel ||
          defaultModel?.model === selectedModel
        }
      >
        {isSavingDefaultModel ? "Saving..." : "Save Default Model"}
      </Button>
    </div>
  );
}
