'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { 
  Bot, 
  FileText, 
  Bookmark, 
  Mail, 
  Filter, 
  MapPin,
  Clock,
  Shield
} from 'lucide-react'

const features = [
  {
    icon: Bot,
    title: 'AI-Powered Matching',
    description: 'Our intelligent algorithm analyzes your profile and preferences to surface the most relevant internship opportunities.',
  },
  {
    icon: FileText,
    title: 'Resume Builder',
    description: 'Create professional resumes with our AI-enhanced templates. Tailor your resume for specific internships automatically.',
  },
  {
    icon: Bookmark,
    title: 'Save & Track',
    description: 'Bookmark interesting opportunities and track your application progress all in one place.',
  },
  {
    icon: Mail,
    title: 'Contact Discovery',
    description: 'Find hiring manager emails and contact information to make direct connections with potential employers.',
  },
  {
    icon: Filter,
    title: 'Advanced Filters',
    description: 'Filter by location, field, salary, company size, and more to find exactly what you\'re looking for.',
  },
  {
    icon: MapPin,
    title: 'Location Flexibility',
    description: 'Search for remote, hybrid, or on-site positions across Canada with detailed location information.',
  },
  {
    icon: Clock,
    title: 'Real-time Updates',
    description: 'Get notified about new opportunities that match your criteria as soon as they\'re posted.',
  },
  {
    icon: Shield,
    title: 'Verified Opportunities',
    description: 'All internships are verified and sourced from reputable job boards and company websites.',
  },
]

export function Features() {
  return (
    <section className="py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            Everything you need to land your dream internship
          </h2>
          <p className="mt-6 text-lg leading-8 text-gray-600">
            Our comprehensive platform provides all the tools and resources you need to find, 
            apply for, and secure the perfect internship opportunity.
          </p>
        </div>
        
        <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
          <div className="grid max-w-xl grid-cols-1 gap-8 lg:max-w-none lg:grid-cols-4">
            {features.map((feature, index) => (
              <Card key={index} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-600">
                    <feature.icon className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle className="text-lg">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-sm leading-6">
                    {feature.description}
                  </CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
