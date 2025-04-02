# Project Brief: Transcript Automation System Frontend

## Project Overview
The Transcript Automation System is a web application designed to automate the processing of YouTube video transcripts, enabling efficient extraction of key information and generation of audio content. The system allows users to input YouTube URLs, process their transcripts using various AI models, and download the processed results.

## Core Requirements

### Functional Requirements
1. Process YouTube video transcripts with customizable prompts
2. Configure and manage API keys for various AI providers
3. Select AI models for transcript processing
4. Save and load prompt templates
5. View and download processed transcripts
6. Generate and download audio files from processed transcripts

### Technical Requirements
1. **Transition to modern tooling**: Migrate from the current structure to a Vite-based React application
2. **Implement shadcn/ui**: Utilize the shadcn/ui component library for consistent UI design
3. **Follow new project structure**: Implement the feature-based architecture defined in .clinerules
4. **Maintain API compatibility**: Ensure the new frontend works with the existing backend API

## Target Users
1. Content creators who need to process YouTube videos for content repurposing
2. Researchers extracting information from video content
3. Educators creating accessible versions of video content
4. Businesses analyzing recorded meetings or presentations

## Key Goals
1. Improve user experience with a modern, responsive UI using shadcn/ui components
2. Enhance maintainability through a well-structured, feature-based code organization
3. Improve performance by leveraging Vite's fast build and development capabilities
4. Maintain all existing functionality while improving the technical foundation

## Project Scope
The project focuses exclusively on the frontend application. The backend API integration will remain unchanged, but the frontend code will be completely restructured according to the new architecture defined in .clinerules.

## Migration Strategy
1. Create a new src directory structure using Vite while preserving the old code in src_old
2. Implement the new project structure following the feature-based organization
3. Gradually migrate functionality from the old structure to the new one
4. Ensure feature parity before replacing the old implementation

## Success Criteria
1. Complete migration to the new project structure
2. Implementation of all existing features using shadcn/ui components
3. Improved performance and user experience
4. Maintainable codebase that follows the standards defined in .clinerules
