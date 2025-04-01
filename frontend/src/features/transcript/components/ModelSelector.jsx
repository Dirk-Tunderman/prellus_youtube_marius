import { useState } from "react";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Check, ChevronsUpDown } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
} from "@/components/ui/command";
import { useTranscriptContext } from "../context/TranscriptContext";
import { useConfigData } from "@/shared/data";
import { toast } from "sonner";

export function ModelSelector() {
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState("");
  const { handleProcessWithModel, isProcessing } = useTranscriptContext();
  const { availableModels, isLoadingAvailableModels } = useConfigData();

  // Group models by provider
  const groupedModels =
    availableModels?.reduce((acc, model) => {
      const provider = model.provider || "Other";
      if (!acc[provider]) {
        acc[provider] = [];
      }
      acc[provider].push(model);
      return acc;
    }, {}) || {};

  const handleSelectModel = (modelId) => {
    setValue(modelId);
    setOpen(false);
  };

  const handleProcessWithSelectedModel = () => {
    if (!value) {
      toast.error("Please select a model first");
      return;
    }

    const result = handleProcessWithModel(value);
    if (!result.success) {
      toast.error(result.error);
      return;
    }

    toast.success("Processing started with selected model!");
  };

  const getModelLabel = (modelId) => {
    if (!modelId) return "Select a model...";

    for (const provider in groupedModels) {
      const model = groupedModels[provider].find((m) => m.value === modelId);
      if (model) return model.label;
    }

    return modelId;
  };

  if (isLoadingAvailableModels) {
    return (
      <Button variant="outline" disabled>
        Loading models...
      </Button>
    );
  }

  if (!availableModels || availableModels.length === 0) {
    return (
      <Button variant="outline" disabled>
        No models available
      </Button>
    );
  }

  return (
    <div className="flex items-center space-x-2">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className="min-w-[200px] justify-between"
            disabled={isProcessing}
          >
            {getModelLabel(value)}
            <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[300px] p-0">
          <Command>
            <CommandInput placeholder="Search models..." />
            <CommandEmpty>No models found.</CommandEmpty>
            {Object.entries(groupedModels).map(([provider, models]) => (
              <CommandGroup key={provider} heading={provider}>
                {models.map((model) => (
                  <CommandItem
                    key={model.value}
                    value={model.value}
                    onSelect={handleSelectModel}
                  >
                    <Check
                      className={cn(
                        "mr-2 h-4 w-4",
                        value === model.value ? "opacity-100" : "opacity-0"
                      )}
                    />
                    {model.label}
                  </CommandItem>
                ))}
              </CommandGroup>
            ))}
          </Command>
        </PopoverContent>
      </Popover>

      {value && (
        <Button
          onClick={handleProcessWithSelectedModel}
          disabled={isProcessing || !value}
          size="sm"
        >
          Process with Model
        </Button>
      )}
    </div>
  );
}
