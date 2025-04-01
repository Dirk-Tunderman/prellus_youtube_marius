<project_guide>
  <title>Simplified Project Structure Guide</title>
  
  <directory_structure>
    <section_title>Directory Structure</section_title>
    <code_block>
src/
├── features/                # Feature-based modules
│   └── [feature]/          # e.g., admin, calculator
│       ├── components/     # Feature-specific components (always flat, no subfolders)
│       │   └── index.js    # Barrel export file
│       ├── context/        # Feature-specific context providers
│       │   └── index.js    # Context barrel export
│       ├── hooks/          # Additional feature-specific hooks (if needed)
│       │   └── index.js    # Hooks barrel export
│       └── index.js        # Feature barrel export
│
├── shared/                 # Cross-feature shared code
│   ├── components/        # Shared UI components (always flat, no subfolders)
│   │   └── index.js       # Barrel export file
│   ├── data/              # ALL data access hooks go here
│   │   └── index.js       # Data hooks barrel export
│   └── index.js           # Shared barrel export
│
├── components/            # UI components
│   └── ui/                # shadcn/ui components (never modify these)
│       └── index.js       # Barrel export file
│
├── lib/                   # Library code
│   └── utils.js           # Utility functions
│
└── core/                  # Application essentials
    ├── router.js         # Single router configuration
    ├── services/         # External service clients folder
    │   └── index.js      # Services barrel export
    ├── state.js          # Application-wide state (when needed)
    └── index.js          # Core barrel export
    </code_block>
  </directory_structure>
  
  <import_rules>
    <section_title>Direct Import Rules</section_title>
    <description>For optimal code organization:</description>
    
    <rule>
      <rule_number>1</rule_number>
      <rule_title>**Direct Data Hook Imports**</rule_title>
      <rule_content>
        - Components and hooks should import shared data hooks directly:
        <code_block>
// CORRECT: Import directly from shared/data
import { useUserData } from '@/shared/data/useUserData';

// AVOID: Don't re-export shared data hooks through feature-level index files
// import { useUserData } from '@/features/admin/hooks'; ❌
        </code_block>
      </rule_content>
    </rule>
    
    <rule>
      <rule_number>2</rule_number>
      <rule_title>**Simple Dependency Chain**</rule_title>
      <rule_content>
        - Maintain a clean, direct dependency path
        - Feature components → Shared data hooks → Core services
      </rule_content>
    </rule>
  </import_rules>
  
  <decision_framework>
    <section_title>Decision Framework: Where Does My Code Go?</section_title>
    <description>When adding new code, follow this simplified decision process:</description>
    
    <infrastructure_decision>
      <subsection_title>1. Is this code infrastructure or configuration?</subsection_title>
      <content>
        If the code configures app-wide behavior or connects to external services, place it in `/core`.

        **Examples:** 
        - Router configuration → `/core/router.js`
        - API/database clients → `/core/services/[service-name].js`
        - Authentication setup → `/core/services/auth.js`
        - Global error handlers → `/core/error.js`
      </content>
    </infrastructure_decision>
    
    <ui_element_decision>
      <subsection_title>2. Is this UI element available in shadcn/ui?</subsection_title>
      <content>
        Check if it already exists in `/components/ui` - never modify these pre-configured components.

        **Examples:** Button, Input, Card, Dialog, Table
      </content>
    </ui_element_decision>
    
    <data_hook_decision>
      <subsection_title>3. Is this a data hook?</subsection_title>
      <content>
        ALL data hooks go in `/shared/data` regardless of how many features currently use them.

        **Examples:** User data, product data, configuration data
      </content>
    </data_hook_decision>
    
    <context_decision>
      <subsection_title>4. Is this feature state shared across components?</subsection_title>
      <content>
        If you need to share state between multiple components in a feature or we need to make the state resistant to route changes, create a context provider:
        
        Place it in `/features/[feature]/context/[Feature]Context.jsx`

        **Examples:** 
        - User selection state shared between list and detail views
        - Form wizard state shared across multiple steps
        - Delete confirmation state shared between list and dialog
        - State that needs to persist across route changes
      </content>
    </context_decision>
    
    <state_isolation_decision>
      <subsection_title>4a. When to isolate state from React Query?</subsection_title>
      <content>
        **Use Pure React Context State (useState):**
        - For UI state that needs to persist across route changes
        - For form state that should not be affected by API cache invalidations
        - When you need predictable state updates independent of network operations
        - For complex multi-step forms or wizards
        - When state needs to be completely isolated from server state
        
        **Use React Query Cache:**
        - For server-derived state that should be synchronized with the backend
        - When you want automatic cache invalidation and refetching
        - For data that should be consistent across the application
        - When optimistic updates are needed for better UX
        - For data that doesn't need to persist across route changes
        
        **Implementation Example:**
        ```jsx
        // Pure React Context State Example
        export function FeatureProvider({ children }) {
          // UI state lives directly in the context using useState
          const [formState, setFormState] = useState({
            field1: "",
            field2: "",
          });
          
          // Use React Query only for server state
          const { serverData, mutateData } = useDataHook();
          
          // Context value with both state types clearly separated
          const contextValue = {
            // UI State (managed by React)
            formState,
            setFormState,
            
            // Server State (managed by React Query)
            serverData,
            mutateData
          };
          
          return (
            <FeatureContext.Provider value={contextValue}>
              {children}
            </FeatureContext.Provider>
          );
        }
        ```
      </content>
    </state_isolation_decision>
    
    <component_decision>
      <subsection_title>5. Is this a new UI component?</subsection_title>
      <content>
        Place it in the feature you're currently working on: `/features/[feature]/components/`.
        Only move to `/shared/components` when actually used by a second feature.

        **Examples:** Feature-specific forms, cards, list items
      </content>
    </component_decision>
  </decision_framework>
  
  <state_management>
    <section_title>State Management Approach</section_title>
    
    <component_state>
      <subsection_title>1. Component State</subsection_title>
      <content>
        **WHEN TO USE:** UI-only state for a single component

        <code_block>
function FeatureComponent() {
  const [isOpen, setIsOpen] = useState(false);
}
        </code_block>
      </content>
    </component_state>
    
    <feature_state>
      <subsection_title>2. Feature State: The Context Provider Pattern</subsection_title>
      <content>
        **WHEN TO USE:** State shared between components in a feature, business logic

        Use the Context Provider Pattern to share state across components:

        <code_block>
// features/admin/context/UserContext.jsx
import { createContext, useContext, useState } from 'react';
import { useUserData } from '@/shared/data/useUserData';

// 1. Create context
const UserContext = createContext(null);

// 2. Create provider component
export function UserProvider({ children }) {
  // Local feature state
  const [selectedUserId, setSelectedUserId] = useState(null);
  
  // Use the shared data hook
  const { users, create, update, delete: deleteUser } = useUserData();
  
  // Add feature-specific business logic
  const createAdmin = (userData) => {
    create({ ...userData, role: 'admin' });
  };
  
  // Transform or filter data for feature needs
  const activeAdmins = users?.filter(user => 
    user.role === 'admin' && user.status === 'active'
  ) || [];
  
  // Create context value
  const contextValue = {
    // From data hook
    users,
    
    // Feature-specific state
    selectedUserId,
    setSelectedUserId,
    
    // Feature-specific business logic
    activeAdmins,
    createAdmin,
    
    // Pass-through operations
    update,
    deleteUser
  };
  
  return (
    <UserContext.Provider value={contextValue}>
      {children}
    </UserContext.Provider>
  );
}

// 3. Create custom hook to use the context
export function useUserContext() {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUserContext must be used within a UserProvider');
  }
  return context;
}

// 4. Usage in components:
// function AdminPage() {
//   return (
//     <UserProvider>
//       <UserList />
//       <UserDetails />
//     </UserProvider>
//   );
// }
        </code_block>
      </content>
    </feature_state>
    
    <application_state>
      <subsection_title>3. Application State</subsection_title>
      <content>
        **WHEN TO USE:** State accessed across multiple features

        For truly cross-feature state, use global context in `/core/state.js`
      </content>
    </application_state>
  </state_management>
  
  <data_hooks>
    <section_title>Data Hook Standardization</section_title>
    
    <shared_data_hooks>
      <subsection_title>1. Shared Data Hooks (in `/shared/data`)</subsection_title>
      <content>
        Use the naming convention `use[Entity]Data` for shared data hooks:

        <code_block>
// shared/data/useUserData.js
import { database } from '@/core/services';
import { toast } from '@/components/ui/sonner';

export function useUserData() {
  const queryClient = useQueryClient();

  // Query for data
  const { data: users, isLoading, error } = useQuery({
    queryKey: ["users"],
    queryFn: async () => {
      const { data, error } = await database.from("users").select("*");
      if (error) throw error;
      return data;
    }
  });

  // Create mutation
  const create = useMutation({
    mutationFn: async (newUser) => {
      const { data, error } = await database.from("users").insert(newUser).select().single();
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(["users"]);
      toast.success("User created successfully");
    },
    onError: (error) => {
      toast.error(`Error: ${error.message}`);
    }
  });
  
  // Return both data and mutations
  return {
    // Data
    users,
    isLoading,
    error,
    
    // Mutations
    create: create.mutate,
    update: update.mutate,
    delete: delete.mutate,
    
    // States
    isCreating: create.isPending,
    isUpdating: update.isPending,
    isDeleting: delete.isPending
  };
}
        </code_block>
      </content>
    </shared_data_hooks>
    
    <component_usage>
      <subsection_title>2. Direct Usage in Components</subsection_title>
      <content>
        Components should import shared data hooks directly:

        <code_block>
// features/admin/components/UserList.jsx
import { useUserData } from '@/shared/data/useUserData';
import { Table } from '@/components/ui/table';

export function UserList() {
  const { users, isLoading } = useUserData();
  
  if (isLoading) return <div>Loading...</div>;
  
  return (
    <Table>
      {/* Table implementation */}
    </Table>
  );
}
        </code_block>
      </content>
    </component_usage>
    
    <context_usage>
      <subsection_title>3. Context Usage in Components</subsection_title>
      <content>
        Components should use the feature context through the custom hook:

        <code_block>
// features/admin/components/UserList.jsx
import { useUserContext } from '@/features/admin/context/UserContext';
import { Table } from '@/components/ui/table';

export function UserList() {
  const { users, isLoading, selectedUserId, setSelectedUserId } = useUserContext();
  
  if (isLoading) return <div>Loading...</div>;
  
  return (
    <Table>
      {users.map(user => (
        <tr 
          key={user.id} 
          className={user.id === selectedUserId ? 'selected' : ''}
          onClick={() => setSelectedUserId(user.id)}
        >
          <td>{user.name}</td>
        </tr>
      ))}
    </Table>
  );
}

// features/admin/components/AdminPage.jsx
import { UserProvider } from '@/features/admin/context/UserContext';
import { UserList } from './UserList';
import { UserDetails } from './UserDetails';

export function AdminPage() {
  return (
    <UserProvider>
      <div className="grid grid-cols-2 gap-4">
        <UserList />
        <UserDetails />
      </div>
    </UserProvider>
  );
}
        </code_block>
      </content>
    </context_usage>
  </data_hooks>
  
  <routing>
    <section_title>Routing: Simple Centralized Approach</section_title>
    <content>
      Use a single router file:

      <code_block>
// core/router.js
import { AdminDashboard, FactorForm } from '@/features/admin/components';
import { Calculator } from '@/features/calculator/components';

export const router = createBrowserRouter([
  { path: '/admin', element: <AdminDashboard /> },
  { path: '/calculator', element: <Calculator /> },
]);
      </code_block>

      Split into feature-based routing only when router file exceeds ~100 lines.
    </content>
  </routing>
  
  <naming_conventions>
    <section_title>File Naming Conventions</section_title>
    <content>
      1. **Components:** Use PascalCase (`FactorForm.jsx`)
      2. **Context Providers:** Use PascalCase with 'Context' suffix (`UserContext.jsx`)
      3. **Context Hooks:** Use camelCase with 'use[Feature]Context' pattern (`useUserContext`)
      4. **Data Hooks:** Use camelCase with 'use[Entity]Data' pattern (`useUserData.js`)
      5. **Utility Hooks:** Use camelCase with 'use' prefix (`useMediaQuery.js`)
      6. **Utility Functions:** Use camelCase (`formatDate.js`)
      7. **Barrel Files:** Always name `index.js`
    </content>
  </naming_conventions>
  
  <ai_assistant>
    <section_title>AI Implementation Assistant</section_title>
    <content>
      When working with AI assistance:

      1. The AI will suggest a directory location for new code by saying:
         "I recommend placing this code in [location] because [reasoning]."

      2. The AI must wait for explicit confirmation before generating or placing code.

      3. If uncertain, the AI should present options:
         "This could belong in either:
         - `/features/admin` if it's specific to admin functionality
         - [...]?
         Which would you prefer?"
    </content>
  </ai_assistant>
</project_guide>
