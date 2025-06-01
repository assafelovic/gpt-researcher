> **Note**: This is a readable copy of the `.cursorrules` file maintained for legibility. The actual rules are implemented from the `.cursorrules` file in the root directory.

# GPT-Researcher Cursor Rules

## Project Overview
This project, named GPT-Researcher, is an LLM-based autonomous agent that conducts local and web research on any topic and generates a comprehensive report with citations. It is built using Next.js and TypeScript, integrating various libraries for their strengths.

Your primary goal is to help with:
- Next.js app router patterns
- TypeScript type safety
- Tailwind CSS best practices
- Code quality standards
- Python/FastAPI backend optimizations

## Key URLs
- Project Home Page: https://gptr.dev/
- GitHub Repository: https://github.com/assafelovic/gpt-researcher
- Documentation: https://docs.gptr.dev/

## Project Structure
- Frontend user interface built with Next.js, TypeScript, and Tailwind CSS in `/frontend`
  - Static FastAPI version for lightweight deployments
  - Next.js version for production use with enhanced features

- Multi-agent research system using LangChain and LangGraph in `/backend/multi_agents`
  - Browser, Editor, Researcher, Reviewer, Revisor, Writer, and Publisher agents
  - Task configuration and agent coordination

- Document processing using Unstructured and PyMuPDF in `/backend/document_processing`
  - PDF, DOCX, and web content parsing
  - Text extraction and preprocessing

- Report generation using LangChain and Jinja2 templates in `/backend/report_generation`
  - Template-based report structuring
  - Dynamic content formatting

- Multiple output formats in `/backend/output_formats`
  - PDF via md2pdf
  - Markdown via mistune
  - DOCX via python-docx
  - Format conversion utilities
  - Export functionality

- GPT Researcher core functionality in `/gpt_researcher`
  - Web scraping and content aggregation
  - Research planning and execution
  - Source validation and tracking
  - Query processing and response generation

- Testing infrastructure in `/tests`
  - Unit tests for individual components
  - Integration tests for agent interactions
  - End-to-end research workflow tests
  - Mock data and fixtures for testing

## Language Model Configuration
- Default model: gpt-4-turbo
- Alternative models: gpt-3.5-turbo, claude-3-opus
- Temperature settings for different tasks
- Context window management
- Token limit handling
- Cost optimization strategies

## Error Handling
- Research failure recovery
- API rate limiting
- Network timeout handling
- Invalid input management
- Source validation errors
- Report generation failures

## Performance
- Parallel processing strategies
- Caching mechanisms
- Memory management
- Response streaming
- Resource allocation
- Query optimization

## Development Workflow
- Branch naming conventions
- Commit message format
- PR review process
- Testing requirements
- Documentation updates
- Version control guidelines

## API Documentation
- REST endpoints
- WebSocket events
- Request/Response formats
- Authentication methods
- Rate limits
- Error codes

## Monitoring
- Performance metrics
- Error tracking
- Usage statistics
- Cost monitoring
- Research quality metrics
- User feedback tracking

## Frontend Components
- Static FastAPI version for lightweight deployments
- Next.js version for production use with enhanced features

## Backend Components
- Multi-agent system architecture
- Document processing pipeline
- Report generation system
- Output format handlers

## Core Research Components
- Web scraping and aggregation
- Research planning and execution
- Source validation
- Query processing

## Testing
- Unit tests
- Integration tests
- End-to-end tests
- Performance testing

## Rule Violation Monitoring
- Alert developer when changes conflict with project structure
- Warn about deviations from coding standards
- Flag unauthorized framework or library additions
- Monitor for security and performance anti-patterns
- Track API usage patterns that may violate guidelines
- Report TypeScript strict mode violations
- Identify accessibility compliance issues

## Development Guidelines
- Use TypeScript with strict mode enabled
- Follow ESLint and Prettier configurations
- Ensure components are responsive and accessible
- Use Tailwind CSS for styling, following the project's design system
- Minimize AI-generated comments, prefer self-documenting code
- Follow React best practices and hooks guidelines
- Validate all user inputs and API responses
- Use existing components as reference implementations

## Important Scripts
- `npm run dev`: Start development server
- `npm run build`: Build for production
- `npm run test`: Run test suite
- `python -m pytest`: Run Python tests
- `python -m uvicorn backend.server.server:app --host=0.0.0.0 --port=8000`: Start FastAPI server
- `python -m uvicorn backend.server.server:app --reload`: Start FastAPI server with auto-reload for development
- `python main.py`: Run the main application directly
- `docker-compose up`: Start all services
- `docker-compose run gpt-researcher-tests`: Run test suite in container

## AI Integration Guidelines
- Prioritize type safety in all AI interactions
- Follow LangChain and LangGraph best practices
- Implement proper error handling for AI responses
- Maintain context window limits
- Handle rate limiting and API quotas
- Validate AI outputs before processing
- Log AI interactions for debugging

## Lexicon
- **GPT Researcher**: Autonomous research agent system
- **Multi-Agent System**: Coordinated AI agents for research tasks
- **Research Pipeline**: End-to-end research workflow
- **Agent Roles**: Browser, Editor, Researcher, Reviewer, Revisor, Writer, Publisher
- **Source Validation**: Verification of research sources
- **Report Generation**: Process of creating final research output

## Additional Resources
- [Next.js Documentation](https://nextjs.org/docs)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [LangChain Documentation](https://python.langchain.com/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Project Documentation](https://docs.gptr.dev/)

_Note: End all your comments with a :-) symbol._ 