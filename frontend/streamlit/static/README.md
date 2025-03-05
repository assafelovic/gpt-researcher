# GPT Researcher Frontend

This is the TypeScript frontend for the GPT Researcher project, an autonomous research agent that conducts local and web research on any topic and generates a comprehensive report with citations.

## Requirements

- Node.js 20.x or higher
- npm 10.x or higher

## Installation

```bash
npm install
```

## Development

To start the development server with automatic compilation:

```bash
npm run watch
```

## Building for Production

To build the production-ready JavaScript files:

```bash
npm run build
```

The compiled JavaScript files will be available in the `dist/js` directory.

## Code Quality

To lint the TypeScript code:

```bash
npm run lint
```

To format the TypeScript code:

```bash
npm run format
```

## Testing

To run the tests:

```bash
npm test
```

## Project Structure

- `ts/` - TypeScript source files
- `dist/` - Compiled JavaScript files
- `css/` - CSS stylesheets
- `index.html` - Main HTML file

## Features

- Dark mode support
- File upload for document analysis
- Research report generation
- Chat functionality for interacting with research results
- Export to multiple formats (PDF, DOCX, Markdown)
- Settings management

## Browser Compatibility

This project supports all modern browsers, including:

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

MIT
