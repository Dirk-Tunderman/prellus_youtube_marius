import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { useTranscriptContext } from "../context/TranscriptContext";
import { TranscriptForm } from "./TranscriptForm";
import { VoiceSelector } from "./VoiceSelector";
import { PromptEditor } from "./PromptEditor";
import { PromptSaveDialog } from "./PromptSaveDialog";
import { PromptListDialog } from "./PromptListDialog";
import { toast } from "sonner";

export function TranscriptPage() {
  const [activeTab, setActiveTab] = useState("basic");
  const transcript = useTranscriptContext();

  const handleSubmit = () => {
    const result = transcript.handleProcessTranscript();
    if (!result.success) {
      toast.error(result.error);
      return;
    }

    toast.success("Processing started successfully!");
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <Tabs
        defaultValue="basic"
        value={activeTab}
        onValueChange={setActiveTab}
        className="w-full"
      >
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="basic">Basic Info</TabsTrigger>
          <TabsTrigger value="prompt">Prompt Configuration</TabsTrigger>
        </TabsList>

        <TabsContent value="basic" className="space-y-4 pt-4">
          <Accordion
            type="multiple"
            defaultValue={["video", "voice"]}
            className="space-y-4"
          >
            <AccordionItem value="video">
              <AccordionTrigger>Video Information</AccordionTrigger>
              <AccordionContent>
                <TranscriptForm />
              </AccordionContent>
            </AccordionItem>
            <AccordionItem value="voice">
              <AccordionTrigger>Voice Settings</AccordionTrigger>
              <AccordionContent>
                <VoiceSelector />
              </AccordionContent>
            </AccordionItem>
          </Accordion>

          <div className="flex justify-between mt-6">
            <Button onClick={handleSubmit} disabled={transcript.isProcessing}>
              {transcript.isProcessing ? "Processing..." : "Process Video"}
            </Button>

            <Button variant="outline" onClick={() => setActiveTab("prompt")}>
              Configure Prompt →
            </Button>
          </div>
        </TabsContent>

        <TabsContent value="prompt" className="space-y-4 pt-4">
          <PromptEditor />

          <div className="flex justify-between mt-6">
            <Button variant="outline" onClick={() => setActiveTab("basic")}>
              ← Back to Basic Info
            </Button>

            <Button onClick={handleSubmit} disabled={transcript.isProcessing}>
              {transcript.isProcessing ? "Processing..." : "Process Video"}
            </Button>
          </div>
        </TabsContent>
      </Tabs>

      {transcript.showSavePrompt && <PromptSaveDialog />}
      {transcript.showPromptList && <PromptListDialog />}
    </div>
  );
}
