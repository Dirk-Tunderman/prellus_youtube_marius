import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Download, Trash2, ChevronDown } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useProjectContext } from "../context/ProjectContext";

export function ProjectCard({ project }) {
  const {
    handleViewTranscript,
    handleDownloadTranscript,
    handleDownloadAudio,
    confirmDelete,
    formatDate,
    formatYoutubeUrl,
    getProjectDisplayName,
    showTranscript,
  } = useProjectContext();

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-start">
          <CardTitle className="text-lg">
            {getProjectDisplayName(project)}
          </CardTitle>
          <div className="flex gap-1">
            {(project.hasTranscript ||
              (project.audioFiles && project.audioFiles.length > 0)) && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-blue-600 hover:bg-blue-50"
                    title="Download options"
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  {project.hasTranscript && (
                    <DropdownMenuItem
                      onClick={() => handleDownloadTranscript(project.id)}
                    >
                      <Download className="mr-2 h-4 w-4" />
                      Download Transcript
                    </DropdownMenuItem>
                  )}
                  {project.audioFiles &&
                    project.audioFiles.length > 0 &&
                    project.audioFiles.map((audioFile) => (
                      <DropdownMenuItem
                        key={audioFile}
                        onClick={() =>
                          handleDownloadAudio(project.id, audioFile)
                        }
                      >
                        <Download className="mr-2 h-4 w-4" />
                        Download Audio
                      </DropdownMenuItem>
                    ))}
                </DropdownMenuContent>
              </DropdownMenu>
            )}
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-red-600 hover:bg-red-50"
              onClick={() => confirmDelete(project)}
              title="Delete project"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
        <div className="text-sm text-muted-foreground">
          {formatDate(project.date)}
        </div>

        {/* Extract YouTube ID from project ID and create URL */}
        {project.id && (
          <a
            href={`https://www.youtube.com/watch?v=${project.id.split("_")[0]}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-blue-600 hover:underline mt-1 block font-medium"
          >
            {`https://www.youtube.com/watch?v=${project.id.split("_")[0]}`}
          </a>
        )}
      </CardHeader>
      <CardContent className="flex-grow pt-0">
        <Separator className="my-2" />
        <div className="flex flex-wrap gap-2 mt-1">
          {project.hasTranscript && (
            <Badge
              variant="outline"
              className="bg-green-50 text-green-700 border-green-200 cursor-pointer hover:bg-green-100"
              onClick={() => handleViewTranscript(project)}
            >
              Transcript
            </Badge>
          )}
          {project.audioFiles && project.audioFiles.length > 0 && (
            <Badge
              variant="outline"
              className="bg-blue-50 text-blue-700 border-blue-200"
            >
              Audio ({project.audioFiles.length})
            </Badge>
          )}
          {!project.hasTranscript &&
            (!project.audioFiles || project.audioFiles.length === 0) && (
              <Badge
                variant="outline"
                className="bg-red-50 text-red-700 border-red-200"
              >
                No Files
              </Badge>
            )}
        </div>
      </CardContent>
    </Card>
  );
}
