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
import { Copy, Download, ArrowLeft, FileText, Hash, Clock } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Separator } from "@/components/ui/separator";

export function TranscriptViewer() {
  const {
    selectedProject,
    transcript,
    isLoadingTranscript,
    setShowTranscript,
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
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={onCopyTranscript}
              disabled={isLoadingTranscript || !transcript?.text}
              title="Copy transcript"
            >
              <Copy className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setShowTranscript(false)}
              title="Close transcript"
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </div>
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

        {!isLoadingTranscript && transcript?.text && (
          <div className="flex items-center gap-4 mt-4 text-lg flex-wrap">
            <Badge
              variant="outline"
              className="py-1.5 px-3 bg-gray-50 border-gray-200"
            >
              <Hash className="mr-2 h-5 w-5 text-gray-500" />
              <span className="font-semibold">
                {transcript.text.length.toLocaleString()}
              </span>
              <span className="ml-1 text-gray-500">characters</span>
            </Badge>
            <Badge
              variant="outline"
              className="py-1.5 px-3 bg-gray-50 border-gray-200"
            >
              <FileText className="mr-2 h-5 w-5 text-gray-500" />
              <span className="font-semibold">
                {transcript.text
                  .split(/\s+/)
                  .filter(Boolean)
                  .length.toLocaleString()}
              </span>
              <span className="ml-1 text-gray-500">words</span>
            </Badge>
            {selectedProject.date && (
              <Badge
                variant="outline"
                className="py-1.5 px-3 bg-gray-50 border-gray-200"
              >
                <Clock className="mr-2 h-5 w-5 text-gray-500" />
                <span className="font-semibold">
                  {(() => {
                    try {
                      // Parse the date string which is in format {'start': 0.14, 'end': 98.76}
                      const dateObj = JSON.parse(
                        selectedProject.date.replace(/'/g, '"')
                      );
                      const durationSeconds = dateObj.end;

                      // Format duration as minutes:seconds
                      const minutes = Math.floor(durationSeconds / 60);
                      const seconds = Math.floor(durationSeconds % 60);
                      return `${minutes}:${seconds
                        .toString()
                        .padStart(2, "0")}`;
                    } catch (e) {
                      return "Unknown";
                    }
                  })()}
                </span>
                <span className="ml-1 text-gray-500">duration</span>
              </Badge>
            )}
          </div>
        )}
      </CardHeader>
      <Separator className="my-2" />
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
    </Card>
  );
}
