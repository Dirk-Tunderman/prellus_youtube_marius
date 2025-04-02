import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useTranscriptContext } from "../context/TranscriptContext";
import { Eraser } from "lucide-react";

export function PromptEditor() {
  const {
    promptData,
    handlePromptChange,
    setShowSavePrompt,
    setShowPromptList,
    isProcessing,
    resetForm,
  } = useTranscriptContext();

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Prompt Configuration</CardTitle>
        <div className="flex space-x-2">
          <Button
            variant="outline"
            onClick={resetForm}
            disabled={isProcessing}
            size="sm"
          >
            <Eraser className="mr-2 h-4 w-4" />
            Clear Form
          </Button>
          <Button
            variant="outline"
            onClick={() => setShowPromptList(true)}
            disabled={isProcessing}
            size="sm"
          >
            Load Prompt
          </Button>
          <Button
            onClick={() => setShowSavePrompt(true)}
            disabled={isProcessing}
            size="sm"
          >
            Save Prompt
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <Accordion
          type="multiple"
          defaultValue={["role", "structure", "tone", "retention"]}
          className="w-full"
        >
          <AccordionItem value="role">
            <AccordionTrigger>Your Role</AccordionTrigger>
            <AccordionContent>
              <Textarea
                value={promptData.yourRole}
                onChange={(e) => handlePromptChange("yourRole", e.target.value)}
                placeholder="Define the role for the script writer (e.g., 'You are a professional scriptwriter...')"
                className="min-h-[100px]"
                disabled={isProcessing}
              />
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="structure">
            <AccordionTrigger>Script Structure</AccordionTrigger>
            <AccordionContent>
              <Textarea
                value={promptData.scriptStructure}
                onChange={(e) =>
                  handlePromptChange("scriptStructure", e.target.value)
                }
                placeholder="Describe how the script should be structured (intro, main sections, conclusion, etc.)"
                className="min-h-[100px]"
                disabled={isProcessing}
              />
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="tone">
            <AccordionTrigger>Tone & Style</AccordionTrigger>
            <AccordionContent>
              <Textarea
                value={promptData.toneAndStyle}
                onChange={(e) =>
                  handlePromptChange("toneAndStyle", e.target.value)
                }
                placeholder="Specify the desired tone and stylistic elements for the script"
                className="min-h-[100px]"
                disabled={isProcessing}
              />
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="retention">
            <AccordionTrigger>Retention & Flow Techniques</AccordionTrigger>
            <AccordionContent>
              <Textarea
                value={promptData.retentionAndFlow}
                onChange={(e) =>
                  handlePromptChange("retentionAndFlow", e.target.value)
                }
                placeholder="Describe techniques to maintain viewer engagement and smooth flow"
                className="min-h-[100px]"
                disabled={isProcessing}
              />
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="additional">
            <AccordionTrigger>Additional Instructions</AccordionTrigger>
            <AccordionContent>
              <Textarea
                value={promptData.additionalInstructions}
                onChange={(e) =>
                  handlePromptChange("additionalInstructions", e.target.value)
                }
                placeholder="Any other specific requirements or instructions"
                className="min-h-[100px]"
                disabled={isProcessing}
              />
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </CardContent>
    </Card>
  );
}
