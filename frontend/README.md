# Chef Candidate Evaluation Frontend

Next.js 15 frontend for the Chef Candidate Evaluation Platform.

## Tech Stack

- **Framework**: Next.js 15 (React 18) with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **State Management**: React Context API
- **API Client**: Axios
- **Video Recording**: react-media-recorder (MediaRecorder API)
- **File Upload**: AWS SDK for JavaScript v3

## Setup

### Prerequisites

- Node.js 20+ or Bun
- Backend API running at http://localhost:8000

### Installation

1. Install dependencies:
```bash
cd frontend
npm install
# or
bun install
```

2. Set up environment variables:
```bash
cp .env.example .env.local
# Edit .env.local with your configuration
```

### Running the Development Server

```bash
npm run dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Building for Production

```bash
npm run build
npm run start
```

### Testing

Run unit tests:
```bash
npm run test
```

Run end-to-end tests:
```bash
npm run test:e2e
```

### Code Quality

Type checking:
```bash
npm run type-check
```

Linting:
```bash
npm run lint
```

## Project Structure

```
frontend/
├── src/
│   ├── app/              # Next.js app router pages
│   ├── components/       # Reusable UI components
│   ├── pages/            # Page components
│   │   ├── candidate/    # Candidate-facing pages
│   │   └── admin/        # Admin-facing pages
│   ├── services/         # API client services
│   ├── lib/              # Utilities
│   └── assets/           # Static assets
├── tests/                # Test suite
└── public/               # Public static files
```

## Features

### Candidate Features
- Account creation and email verification
- Document upload (resume, cover letter)
- Video interview recording with automatic transcription
- Menu review with ratings, comments, and dish proposals

### Admin Features
- Candidate review dashboard
- Gallery and table views for feedback comparison
- Interview prompt management
- Candidate status tracking

## Environment Variables

See `.env.example` for all available configuration options.

## Mobile-First Design

The application is designed mobile-first with responsive breakpoints:
- Mobile: < 640px (1 column gallery)
- Tablet: 640px - 1024px (2 columns gallery)
- Desktop: 1024px - 1280px (3 columns gallery)
- Wide: > 1280px (4 columns gallery)
