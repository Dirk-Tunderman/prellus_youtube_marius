import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useProjectContext } from "../context/ProjectContext";
import { toast } from "sonner";

export function DeleteConfirmDialog() {
  const {
    projectToDelete,
    handleDeleteProject,
    cancelDelete,
    getProjectDisplayName,
    isDeleting,
  } = useProjectContext();

  console.log(
    "[DeleteConfirmDialog] Rendering with projectToDelete:",
    projectToDelete
  );

  if (!projectToDelete) {
    console.log("[DeleteConfirmDialog] No projectToDelete, returning null");
    return null;
  }

  const onDeleteProject = () => {
    const result = handleDeleteProject();
    if (!result.success) {
      toast.error(result.error);
      return;
    }

    toast.success("Project deleted successfully!");
  };

  return (
    <Dialog open={true} onOpenChange={cancelDelete}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Delete Project</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete "
            {getProjectDisplayName(projectToDelete)}"? This action cannot be
            undone and all associated files will be permanently removed.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={cancelDelete}
            disabled={isDeleting}
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={onDeleteProject}
            disabled={isDeleting}
          >
            {isDeleting ? "Deleting..." : "Delete"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
