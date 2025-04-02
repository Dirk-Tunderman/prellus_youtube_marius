import { useProjectContext } from "../context/ProjectContext";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Copy, Download, ArrowLeft } from "lucide-react";
import { toast } from "sonner";

export function TranscriptViewer() {
  const {
    selectedProject,
    transcript,
    isLoadingTranscript,
    setShowTranscript,
    handleDownloadTranscript,
    copyTranscript,
    getProjectDisplayName,
  } = useProjectContext();

  if (!selectedProject) {
    return null;
  }

  const onCopyTranscript = () => {
    const result = copyTranscript();
    if (!result.success) {
      toast.error(result.error);
      return;
    }

    toast.success("Transcript copied to clipboard!");
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <CardTitle>{getProjectDisplayName(selectedProject)}</CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowTranscript(false)}
            className="lg:hidden"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to List
          </Button>
        </div>
        {selectedProject.url && (
          <div className="text-sm">
            <a
              href={selectedProject.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              {selectedProject.url}
            </a>
          </div>
        )}
      </CardHeader>
      <CardContent className="flex-grow overflow-hidden">
        {isLoadingTranscript ? (
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
          </div>
        ) : (
          <div className="bg-muted p-4 rounded-md h-full overflow-y-auto">
            <pre className="whitespace-pre-wrap font-mono text-sm leading-relaxed">
              {transcript?.text || "No transcript content available."}
            </pre>
          </div>
        )}
      </CardContent>
      <CardFooter className="pt-4 flex justify-between">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowTranscript(false)}
          className="hidden lg:flex"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to List
        </Button>
        <div className="flex space-x-2 ml-auto">
          <Button
            variant="outline"
            size="sm"
            onClick={onCopyTranscript}
            disabled={isLoadingTranscript || !transcript?.text}
          >
            <Copy className="mr-2 h-4 w-4" />
            Copy
          </Button>
          <Button
            variant="default"
            size="sm"
            onClick={() => handleDownloadTranscript(selectedProject.id)}
            disabled={isLoadingTranscript || !transcript?.text}
          >
            <Download className="mr-2 h-4 w-4" />
            Download
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}
