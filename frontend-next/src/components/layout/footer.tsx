'use client'

import Link from 'next/link'
import { Briefcase } from 'lucide-react'

const navigation = {
  main: [
    { name: 'Browse Jobs', href: '/browse' },
    { name: 'Resume Builder', href: '/resume' },
    { name: 'About', href: '/about' },
    { name: 'Contact', href: '/contact' },
  ],
  legal: [
    { name: 'Privacy Policy', href: '/privacy' },
    { name: 'Terms of Service', href: '/terms' },
    { name: 'Cookie Policy', href: '/cookies' },
  ],
}

export function Footer() {
  return (
    <footer className="bg-white border-t">
      <div className="mx-auto max-w-7xl overflow-hidden px-6 py-20 sm:py-24 lg:px-8">
        <div className="flex justify-center">
          <Link href="/" className="flex items-center space-x-2">
            <Briefcase className="h-8 w-8 text-blue-600" />
            <span className="text-xl font-bold text-gray-900">EasyInterns</span>
          </Link>
        </div>
        
        <nav className="-mb-6 columns-2 sm:flex sm:justify-center sm:space-x-12 mt-10" aria-label="Footer">
          {navigation.main.map((item) => (
            <div key={item.name} className="pb-6">
              <Link href={item.href} className="text-sm leading-6 text-gray-600 hover:text-gray-900">
                {item.name}
              </Link>
            </div>
          ))}
        </nav>
        
        <div className="mt-10 flex justify-center space-x-10">
          {navigation.legal.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              className="text-xs leading-5 text-gray-500 hover:text-gray-600"
            >
              {item.name}
            </Link>
          ))}
        </div>
        
        <p className="mt-10 text-center text-xs leading-5 text-gray-500">
          &copy; 2024 EasyInterns. All rights reserved. Helping students find their perfect internship.
        </p>
      </div>
    </footer>
  )
}
