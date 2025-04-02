import { useConfigManagement } from "../hooks";
import { ProviderCard } from "./ProviderCard";
import { getProviderById } from "@/core/registry/models";

export function ApiKeyManager() {
  const { availableProviders } = useConfigManagement();

  return (
    <div className="space-y-4">
      {availableProviders.map((provider) => {
        const providerInfo = getProviderById(provider.id);
        return (
          <ProviderCard
            key={provider.id}
            provider={provider.id}
            displayName={providerInfo.name}
            description={providerInfo.description}
          />
        );
      })}
    </div>
  );
}
