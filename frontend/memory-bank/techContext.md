# Technical Context: Transcript Automation System Frontend

## Technologies Used

### Core Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.2.0 | UI library for building component-based interfaces |
| Vite | 6.2.4 | Build tool and development server |
| React Router | Latest | Client-side routing |
| Axios | Latest | HTTP client for API requests |
| shadcn/ui | Latest | Component library based on Radix UI and Tailwind CSS |

### Additional Libraries

| Library | Purpose |
|---------|---------|
| React Query | Data fetching, caching, and state management |
| Tailwind CSS | v3.x - Utility-first CSS framework |
| Radix UI | Unstyled, accessible UI components |
| Zod | Schema validation |
| Lucide React | Icon library |
| React Hook Form | Form state management and validation |

## Development Setup

### Prerequisites
- Node.js 18+ and npm/yarn
- Git for version control
- Modern web browser (Chrome, Firefox, Edge)

### Local Development
1. Clone the repository
2. Install dependencies: `npm install`
3. Start development server: `npm run dev`
4. Access the application at `http://localhost:5173`

### Build Process
1. Create production build: `npm run build`
2. Preview production build: `npm run preview`

### Environment Variables
- `VITE_API_URL`: Backend API URL (default: http://localhost:5001/api)

## API Integration

The frontend communicates with a RESTful backend API that provides the following services:

### Transcript Services
- `POST /api/transcripts/process`: Process a YouTube video transcript
- `GET /api/transcripts`: Get all processed transcripts
- `POST /api/transcripts/process/model`: Process with a specific model

### Audio Services
- `POST /api/audio/generate/:transcriptId`: Generate audio from a transcript

### Prompt Services
- `POST /api/prompts/save`: Save a prompt template
- `GET /api/prompts`: Get all saved prompts
- `GET /api/prompts/:promptId`: Get a specific prompt
- `DELETE /api/prompts/:promptId`: Delete a prompt

### Project Services
- `GET /api/projects`: Get all projects
- `GET /api/projects/:projectId/transcript`: Get transcript for a project
- `GET /api/projects/:projectId/transcript/download`: Download transcript file
- `GET /api/projects/:projectId/audio/:filename`: Download audio file
- `DELETE /api/projects/:projectId`: Delete a project

### Configuration Services
- `GET /api/config/apikeys`: Get API key configuration
- `POST /api/config/apikeys`: Save an API key
- `DELETE /api/config/apikeys/:provider`: Delete an API key
- `GET /api/config/defaultmodel`: Get default model
- `POST /api/config/defaultmodel`: Set default model
- `GET /api/config/models`: Get available models

## Technical Constraints

### Browser Compatibility
- The application must support modern browsers (Chrome, Firefox, Safari, Edge)
- No support required for Internet Explorer

### API Compatibility
- The frontend must maintain compatibility with the existing backend API
- API endpoints and request/response formats cannot be changed

### Performance Requirements
- Initial load time should be under 2 seconds on broadband connections
- UI interactions should feel responsive (< 100ms)
- Large transcript processing should show appropriate loading states

## Dependencies and External Services

### AI Service Providers
The application integrates with multiple AI service providers:
- OpenAI (GPT models)
- Google (Gemini models)
- Anthropic (Claude models)
- DeepSeek
- Qwen

### YouTube API
- Used for extracting video metadata and transcripts

### Text-to-Speech Services
- Used for generating audio from processed transcripts

## Migration Considerations

## Tooling Changes

### From Create React App to Vite
- Faster development server with HMR
- More efficient build process
- Better developer experience

### From CSS-in-JS to Tailwind CSS
- More consistent styling
- Better performance
- Easier theming

## Deployment Considerations

### Build Output
- Vite produces optimized static assets in the `dist` directory
- Assets include HTML, CSS, JavaScript, and other static files

### Hosting Options
- Static hosting (Netlify, Vercel, GitHub Pages)
- Traditional web servers (Apache, Nginx)
- Container-based deployment (Docker)

### CI/CD Integration
- Build and test on each pull request
- Automated deployment on merge to main branch
