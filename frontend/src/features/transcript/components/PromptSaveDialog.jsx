import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useTranscriptContext } from "../context/TranscriptContext";
import { toast } from "sonner";

export function PromptSaveDialog() {
  const {
    promptName,
    setPromptName,
    handleSavePrompt,
    setShowSavePrompt,
    isSaving,
  } = useTranscriptContext();

  const onSave = () => {
    const result = handleSavePrompt();
    if (!result.success) {
      toast.error(result.error);
      return;
    }

    toast.success("Prompt saved successfully!");
  };

  return (
    <Dialog open={true} onOpenChange={() => setShowSavePrompt(false)}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Save Prompt Template</DialogTitle>
          <DialogDescription>
            Save your current prompt configuration for future use.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="promptName" className="text-right">
              Name
            </Label>
            <Input
              id="promptName"
              value={promptName}
              onChange={(e) => setPromptName(e.target.value)}
              placeholder="Enter a name for this prompt"
              className="col-span-3"
              autoFocus
            />
          </div>
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => setShowSavePrompt(false)}
            disabled={isSaving}
          >
            Cancel
          </Button>
          <Button onClick={onSave} disabled={isSaving}>
            {isSaving ? "Saving..." : "Save"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
