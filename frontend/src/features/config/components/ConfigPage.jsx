import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ApiKeyManager } from "./ApiKeyManager";
import { DefaultModelSelector } from "./DefaultModelSelector";
import { useConfigManagement } from "../hooks";

export function ConfigPage() {
  return (
    <div className="container mx-auto py-6 space-y-8">
      <div className="space-y-8">
        <Card>
          <CardHeader>
            <CardTitle>Default Model Selection</CardTitle>
            <CardDescription>
              Select the default AI model to use for processing transcripts.
              This model will be used unless overridden for a specific task.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DefaultModelSelector />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>API Key Management</CardTitle>
            <CardDescription>
              Configure your API keys for various AI services. These keys are
              required for transcript processing and audio generation. The keys
              will be securely stored in the server's environment variables and
              .env file.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ApiKeyManager />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
