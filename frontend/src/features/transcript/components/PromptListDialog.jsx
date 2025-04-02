import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useTranscriptContext } from "../context/TranscriptContext";
import { formatDate } from "@/lib/utils";
import { toast } from "sonner";
import { Search, Trash2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { useState } from "react";

export function PromptListDialog() {
  const {
    prompts,
    handleLoadPrompt,
    handleDeletePrompt,
    setShowPromptList,
    isDeleting,
  } = useTranscriptContext();
  const [searchTerm, setSearchTerm] = useState("");
  const [promptToDelete, setPromptToDelete] = useState(null);

  const filteredPrompts =
    prompts?.filter((prompt) =>
      prompt.prompt_name.toLowerCase().includes(searchTerm.toLowerCase())
    ) || [];

  const onLoadPrompt = async (promptId) => {
    const result = await handleLoadPrompt(promptId);
    if (!result.success) {
      toast.error(result.error);
      return;
    }

    toast.success("Prompt loaded successfully!");
  };

  const onDeletePrompt = (promptId) => {
    const result = handleDeletePrompt(promptId);
    if (!result.success) {
      toast.error(result.error);
      return;
    }

    toast.success("Prompt deleted successfully!");
    setPromptToDelete(null);
  };

  return (
    <>
      <Dialog open={true} onOpenChange={() => setShowPromptList(false)}>
        <DialogContent className="sm:max-w-[525px]">
          <DialogHeader>
            <DialogTitle>Saved Prompts</DialogTitle>
            <DialogDescription>
              Select a prompt template to load into the editor.
            </DialogDescription>
          </DialogHeader>

          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search prompts..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8"
            />
          </div>

          <ScrollArea className="h-[300px] rounded-md border p-4">
            {filteredPrompts.length === 0 ? (
              <div className="flex h-full items-center justify-center text-center text-muted-foreground">
                {searchTerm
                  ? "No prompts match your search"
                  : "No saved prompts found"}
              </div>
            ) : (
              <div className="space-y-4">
                {filteredPrompts.map((prompt) => (
                  <div
                    key={prompt.unique_id}
                    className="flex flex-col space-y-2 rounded-lg border p-3 hover:bg-accent"
                  >
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium">{prompt.prompt_name}</h4>
                      <div className="flex items-center space-x-2">
                        <Button
                          size="sm"
                          onClick={() => onLoadPrompt(prompt.unique_id)}
                        >
                          Load
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setPromptToDelete(prompt.unique_id)}
                          disabled={isDeleting}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {formatDate(prompt.date)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </DialogContent>
      </Dialog>

      {promptToDelete && (
        <AlertDialog
          open={!!promptToDelete}
          onOpenChange={() => setPromptToDelete(null)}
        >
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Are you sure?</AlertDialogTitle>
              <AlertDialogDescription>
                This action cannot be undone. This will permanently delete the
                prompt template.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={() => onDeletePrompt(promptToDelete)}
                disabled={isDeleting}
              >
                {isDeleting ? "Deleting..." : "Delete"}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}
    </>
  );
}
