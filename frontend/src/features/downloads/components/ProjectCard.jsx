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

  // Debug logging for date
  console.log(`ProjectCard for ${project.id} - date:`, project.date);
  
  // Extract date from project ID if needed
  const getDateFromId = (id) => {
    if (!id || !id.includes('_') || id.split('_').length < 3) {
      return null;
    }
    
    const parts = id.split('_');
    const datePart = parts[1]; // YYYYMMDD
    const timePart = parts[2]; // HHMMSS
    
    if (datePart.length === 8 && timePart.length === 6) {
      const year = datePart.substring(0, 4);
      const month = datePart.substring(4, 6);
      const day = datePart.substring(6, 8);
      
      const hour = timePart.substring(0, 2);
      const minute = timePart.substring(2, 4);
      
      // Create date object
      const dateObj = new Date(`${year}-${month}-${day}T${hour}:${minute}:00`);
      
      // Format the date for display
      if (!isNaN(dateObj.getTime())) {
        return dateObj.toLocaleString("en-US", {
          year: "numeric",
          month: "long",
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        });
      }
    }
    
    return null;
  };
  
  // Get date display string - try from project.date first, then fall back to ID
  const getDateDisplay = () => {
    // Try using the formatDate utility first
    const formattedDate = formatDate(project.date);
    
    // If it returned one of our error strings, try extracting from ID
    if (formattedDate === "Invalid date" || 
        formattedDate === "Date not available" || 
        formattedDate === "Error formatting date") {
      const dateFromId = getDateFromId(project.id);
      return dateFromId || formattedDate;
    }
    
    return formattedDate;
  };

  return (
    <Card className="h-full flex flex-col" data-project-id={project.id}>
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
          {getDateDisplay()}
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
