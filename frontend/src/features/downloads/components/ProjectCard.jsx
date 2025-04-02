import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Download, Trash2, Eye } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useProjectContext } from "../context/ProjectContext";
import { MoreHorizontal } from "lucide-react";

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
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {project.hasTranscript && (
                <DropdownMenuItem onClick={() => handleViewTranscript(project)}>
                  <Eye className="mr-2 h-4 w-4" />
                  View Transcript
                </DropdownMenuItem>
              )}
              {project.hasTranscript && (
                <DropdownMenuItem
                  onClick={() => handleDownloadTranscript(project.id)}
                >
                  <Download className="mr-2 h-4 w-4" />
                  Download Transcript
                </DropdownMenuItem>
              )}
              <DropdownMenuItem
                onClick={() => confirmDelete(project)}
                className="text-red-600"
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete Project
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
        <div className="text-sm text-muted-foreground">
          {formatDate(project.date)}
        </div>
        {project.url && (
          <a
            href={project.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-blue-600 hover:underline mt-1 block"
          >
            {formatYoutubeUrl(project.url)}
          </a>
        )}
      </CardHeader>
      <CardContent className="flex-grow">
        <div className="flex flex-wrap gap-2 mt-1">
          {project.hasTranscript && (
            <Badge
              variant="outline"
              className="bg-green-50 text-green-700 border-green-200"
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
      {project.audioFiles && project.audioFiles.length > 0 && (
        <CardFooter className="pt-0 flex flex-wrap gap-2">
          {project.audioFiles.map((audioFile) => (
            <Button
              key={audioFile}
              variant="outline"
              size="sm"
              onClick={() => handleDownloadAudio(project.id, audioFile)}
              className="text-blue-600"
            >
              <Download className="mr-2 h-4 w-4" />
              Download Audio
            </Button>
          ))}
        </CardFooter>
      )}
    </Card>
  );
}
