# EasyInterns Frontend

Modern Next.js 14 frontend for the EasyInterns platform built with TypeScript, Tailwind CSS, and shadcn/ui.

## Features

- 🚀 Next.js 14 with App Router
- 💎 TypeScript for type safety
- 🎨 Tailwind CSS for styling
- 🧩 shadcn/ui component library
- 🔐 Supabase authentication
- 📊 TanStack Query for data fetching
- 🗄️ Zustand for state management
- 📱 Fully responsive design

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Supabase project set up

### Installation

1. Install dependencies:
```bash
npm install
```

2. Copy environment variables:
```bash
cp .env.example .env.local
```

3. Update `.env.local` with your Supabase credentials:
```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. Run the development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Project Structure

```
src/
├── app/                 # Next.js 14 app router pages
├── components/          # React components
│   ├── ui/             # shadcn/ui components
│   ├── layout/         # Layout components
│   └── sections/       # Page sections
├── lib/                # Utility libraries
│   ├── api.ts          # API client
│   ├── supabase.ts     # Supabase client
│   ├── store.ts        # Zustand stores
│   └── utils.ts        # Utility functions
└── types/              # TypeScript type definitions
```

## Key Pages

- `/` - Landing page with hero, features, and CTA
- `/browse` - Internship search and filtering
- `/internships/[id]` - Individual internship details
- `/resume` - Resume builder and management
- `/saved` - Bookmarked internships
- `/profile` - User profile and preferences
- `/auth/signin` - Authentication pages

## API Integration

The frontend integrates with the FastAPI backend through:

- RESTful API endpoints for internships, users, resumes
- Supabase authentication with JWT tokens
- Real-time updates for scraping jobs
- File uploads for resume PDFs

## Deployment

### Vercel (Recommended)

1. Connect your GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push to main branch

### Manual Build

```bash
npm run build
npm start
```

## Development

### Adding New Components

Use shadcn/ui CLI to add new components:

```bash
npx shadcn-ui@latest add [component-name]
```

### Code Quality

- ESLint for code linting
- TypeScript for type checking
- Prettier for code formatting (recommended)

### Testing

```bash
npm run lint        # Run ESLint
npm run type-check  # Run TypeScript compiler
```
