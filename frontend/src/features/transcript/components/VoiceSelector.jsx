import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import { useTranscriptContext } from "../context/TranscriptContext";
import { getAllVoices } from "@/core/registry/voices";
import { VoiceSearchDialog } from "./VoiceSearchDialog";

export function VoiceSelector() {
  const { voice, setVoice, speed, setSpeed, isProcessing } =
    useTranscriptContext();
  const [open, setOpen] = useState(false);

  // Get the selected voice details
  const selectedVoice = getAllVoices().find((v) => v.value === voice);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Voice Settings</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <Label>Voice</Label>
          <VoiceSearchDialog
            open={open}
            onOpenChange={setOpen}
            selectedVoice={selectedVoice}
            onSelectVoice={setVoice}
            isProcessing={isProcessing}
          />
        </div>

        <div className="space-y-2">
          <div className="flex justify-between">
            <Label htmlFor="speed-slider">Speed: {speed.toFixed(1)}</Label>
          </div>
          <Slider
            id="speed-slider"
            min={0.5}
            max={1.0}
            step={0.1}
            value={[speed]}
            onValueChange={(values) => setSpeed(values[0])}
            disabled={isProcessing}
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>0.5</span>
            <span>1.0</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
