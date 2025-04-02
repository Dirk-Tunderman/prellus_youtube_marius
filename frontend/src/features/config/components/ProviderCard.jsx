import { useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Eye, EyeOff } from "lucide-react";
import { useConfigManagement } from "../hooks";
import { toast } from "sonner";

export function ProviderCard({ provider, displayName, description }) {
  const [showKey, setShowKey] = useState(false);
  const {
    newApiKey,
    handleApiKeyChange,
    handleSaveApiKey,
    handleDeleteApiKey,
    isProviderConfigured,
    getModelsForProvider,
    isSavingApiKey,
    isDeletingApiKey,
  } = useConfigManagement();

  const configured = isProviderConfigured(provider);
  const models = getModelsForProvider(provider);

  const onSaveApiKey = () => {
    const result = handleSaveApiKey(provider);
    if (!result.success) {
      toast.error(result.error);
      return;
    }

    toast.success(`${displayName} API key saved successfully!`);
  };

  const onDeleteApiKey = () => {
    const result = handleDeleteApiKey(provider);
    if (!result.success) {
      toast.error(result.error);
      return;
    }

    toast.success(`${displayName} API key deleted successfully!`);
  };

  return (
    <Card className={configured ? "border-green-200" : "border-gray-200"}>
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <CardTitle>{displayName} API Key</CardTitle>
          {configured && (
            <Badge
              variant="outline"
              className="bg-green-50 text-green-700 border-green-200"
            >
              Configured
            </Badge>
          )}
        </div>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex space-x-2">
          <div className="relative flex-1">
            <Input
              type={showKey ? "text" : "password"}
              value={newApiKey.provider === provider ? newApiKey.key : ""}
              onChange={(e) => handleApiKeyChange(provider, e.target.value)}
              placeholder={
                configured
                  ? "••••••••••••••••••••••"
                  : `Enter your ${displayName} API key`
              }
            />
            <button
              type="button"
              onClick={() => setShowKey(!showKey)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
            >
              {showKey ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
          <Button onClick={onSaveApiKey} disabled={isSavingApiKey}>
            Save
          </Button>
          {configured && (
            <Button
              variant="destructive"
              onClick={onDeleteApiKey}
              disabled={isDeletingApiKey}
            >
              Delete
            </Button>
          )}
        </div>
      </CardContent>
      {configured && models.length > 0 && (
        <CardFooter className="pt-0 text-sm text-muted-foreground">
          <div>
            <strong>Available models:</strong>{" "}
            {models.map((m) => m.label).join(", ")}
          </div>
        </CardFooter>
      )}
    </Card>
  );
}
