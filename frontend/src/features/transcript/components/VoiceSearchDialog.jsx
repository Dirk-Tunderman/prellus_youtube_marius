import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import { Button } from "@/components/ui/button";
import { Check, ChevronsUpDown, Search } from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { voices, getAllVoices } from "@/core/registry/voices";

export function VoiceSearchDialog({
  open,
  onOpenChange,
  selectedVoice,
  onSelectVoice,
  isProcessing,
}) {
  const [filter, setFilter] = useState({
    accent: "all",
    gender: "all",
  });

  // Filter voices based on current filters
  const filteredVoices = {
    american: voices.american.filter(
      (v) =>
        filter.gender === "all" ||
        (filter.gender === "male" && v.value.startsWith("am_")) ||
        (filter.gender === "female" && v.value.startsWith("af_"))
    ),
    british: voices.british.filter(
      (v) =>
        filter.gender === "all" ||
        (filter.gender === "male" && v.value.startsWith("bm_")) ||
        (filter.gender === "female" && v.value.startsWith("bf_"))
    ),
  };

  // Determine which accent groups to show
  const showAmerican = filter.accent === "all" || filter.accent === "american";
  const showBritish = filter.accent === "all" || filter.accent === "british";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-full justify-between"
          disabled={isProcessing}
        >
          {selectedVoice ? selectedVoice.label : "Select a voice..."}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </DialogTrigger>
      <DialogContent className="w-[60%] max-w-[800px] p-0 gap-0">
        <Command className="h-[450px] rounded-lg border-0 shadow-none">
          <DialogHeader className="px-4 pt-4 pb-0">
            <DialogTitle className="text-xl font-semibold mb-2">Select Voice</DialogTitle>
            <div className="flex items-center border rounded-md px-3 focus-within:ring-1 focus-within:ring-ring">
              <Search className="mr-2 h-4 w-4 shrink-0 opacity-50" />
              <CommandInput 
                placeholder="Search voices..." 
                className="flex-1 border-0 px-0 py-2 focus-visible:ring-0 focus-visible:ring-offset-0" 
              />
            </div>
          </DialogHeader>
          
          <div className="flex flex-wrap gap-1 px-4 py-3 mt-2">
            <Badge
              variant={filter.accent === "all" ? "default" : "outline"}
              className="cursor-pointer"
              onClick={() => setFilter((f) => ({ ...f, accent: "all" }))}
            >
              All Accents
            </Badge>
            <Badge
              variant={filter.accent === "american" ? "default" : "outline"}
              className="cursor-pointer"
              onClick={() => setFilter((f) => ({ ...f, accent: "american" }))}
            >
              American
            </Badge>
            <Badge
              variant={filter.accent === "british" ? "default" : "outline"}
              className="cursor-pointer"
              onClick={() => setFilter((f) => ({ ...f, accent: "british" }))}
            >
              British
            </Badge>

            <Badge
              variant={filter.gender === "all" ? "default" : "outline"}
              className="cursor-pointer"
              onClick={() => setFilter((f) => ({ ...f, gender: "all" }))}
            >
              All Genders
            </Badge>
            <Badge
              variant={filter.gender === "female" ? "default" : "outline"}
              className="cursor-pointer"
              onClick={() => setFilter((f) => ({ ...f, gender: "female" }))}
            >
              Female
            </Badge>
            <Badge
              variant={filter.gender === "male" ? "default" : "outline"}
              className="cursor-pointer"
              onClick={() => setFilter((f) => ({ ...f, gender: "male" }))}
            >
              Male
            </Badge>
          </div>
          
          <CommandSeparator />
          
          <CommandList className="px-2 py-2 overflow-auto">
            <CommandEmpty className="py-6 text-center">No voice found.</CommandEmpty>

            {showAmerican && filteredVoices.american.length > 0 && (
              <CommandGroup 
                heading="American English" 
                className="px-2 py-1"
                headingClassName="text-sm font-medium text-muted-foreground"
              >
                {filteredVoices.american.map((voiceOption) => (
                  <CommandItem
                    key={voiceOption.value}
                    value={voiceOption.value}
                    onSelect={(value) => {
                      onSelectVoice(value);
                      onOpenChange(false);
                    }}
                  >
                    <Check
                      className={cn(
                        "mr-2 h-4 w-4",
                        selectedVoice?.value === voiceOption.value
                          ? "opacity-100"
                          : "opacity-0"
                      )}
                    />
                    {voiceOption.label}
                  </CommandItem>
                ))}
              </CommandGroup>
            )}

            {showBritish && filteredVoices.british.length > 0 && (
              <CommandGroup 
                heading="British English" 
                className="px-2 py-1"
                headingClassName="text-sm font-medium text-muted-foreground"
              >
                {filteredVoices.british.map((voiceOption) => (
                  <CommandItem
                    key={voiceOption.value}
                    value={voiceOption.value}
                    onSelect={(value) => {
                      onSelectVoice(value);
                      onOpenChange(false);
                    }}
                  >
                    <Check
                      className={cn(
                        "mr-2 h-4 w-4",
                        selectedVoice?.value === voiceOption.value
                          ? "opacity-100"
                          : "opacity-0"
                      )}
                    />
                    {voiceOption.label}
                  </CommandItem>
                ))}
              </CommandGroup>
            )}
          </CommandList>
        </Command>
      </DialogContent>
    </Dialog>
  );
}
