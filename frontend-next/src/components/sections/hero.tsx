'use client'

import { Button } from '@/components/ui/button'
import { Search, Briefcase, Users, TrendingUp } from 'lucide-react'
import Link from 'next/link'

export function Hero() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-indigo-50 py-20 sm:py-32">
      <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0))]" />
      
      <div className="relative mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl">
            Find Your Perfect{' '}
            <span className="text-blue-600">Internship</span>
          </h1>
          
          <p className="mt-6 text-lg leading-8 text-gray-600">
            AI-powered internship search platform connecting students with top companies across Canada. 
            Discover opportunities, build your resume, and launch your career.
          </p>
          
          <div className="mt-10 flex items-center justify-center gap-x-6">
            <Button asChild size="lg" className="px-8 py-3">
              <Link href="/browse">
                <Search className="mr-2 h-4 w-4" />
                Start Searching
              </Link>
            </Button>
            
            <Button variant="outline" size="lg" asChild>
              <Link href="/resume">
                Build Resume
              </Link>
            </Button>
          </div>
        </div>
        
        <div className="mt-16 flow-root sm:mt-24">
          <div className="relative rounded-xl bg-gray-900/5 p-2 ring-1 ring-inset ring-gray-900/10 lg:rounded-2xl lg:p-4">
            <div className="aspect-[16/9] rounded-md bg-white shadow-2xl ring-1 ring-gray-900/10">
              <div className="flex h-full items-center justify-center">
                <div className="text-center">
                  <Briefcase className="mx-auto h-12 w-12 text-blue-600" />
                  <p className="mt-2 text-sm text-gray-500">Interactive Dashboard Preview</p>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-4xl">
          <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-10 lg:max-w-none lg:grid-cols-3 lg:gap-y-16">
            <div className="relative pl-16">
              <dt className="text-base font-semibold leading-7 text-gray-900">
                <div className="absolute left-0 top-0 flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600">
                  <Search className="h-6 w-6 text-white" />
                </div>
                Smart Search
              </dt>
              <dd className="mt-2 text-base leading-7 text-gray-600">
                AI-powered matching algorithm finds internships that align with your skills and career goals.
              </dd>
            </div>
            
            <div className="relative pl-16">
              <dt className="text-base font-semibold leading-7 text-gray-900">
                <div className="absolute left-0 top-0 flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600">
                  <Users className="h-6 w-6 text-white" />
                </div>
                Top Companies
              </dt>
              <dd className="mt-2 text-base leading-7 text-gray-600">
                Access opportunities from leading tech companies, startups, and government organizations.
              </dd>
            </div>
            
            <div className="relative pl-16">
              <dt className="text-base font-semibold leading-7 text-gray-900">
                <div className="absolute left-0 top-0 flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600">
                  <TrendingUp className="h-6 w-6 text-white" />
                </div>
                Career Growth
              </dt>
              <dd className="mt-2 text-base leading-7 text-gray-600">
                Build your professional network and gain valuable experience to accelerate your career.
              </dd>
            </div>
          </dl>
        </div>
      </div>
    </section>
  )
}
