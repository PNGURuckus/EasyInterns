'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createClient } from '@/lib/supabase'
import { useAuthStore } from '@/lib/store'
import { useEffect, useState } from 'react'
import { apiClient } from '@/lib/api'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      refetchOnWindowFocus: false,
    },
  },
})

export function Providers({ children }: { children: React.ReactNode }) {
  const { setUser, setLoading } = useAuthStore()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    
    const supabase = createClient()
    
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session?.user) {
        // Set API token
        apiClient.setToken(session.access_token)
        
        // Fetch user profile
        apiClient.getProfile().then((response) => {
          if (response.success && response.data) {
            setUser(response.data)
          } else {
            setUser(null)
          }
        })
      } else {
        setUser(null)
      }
    })

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (event === 'SIGNED_IN' && session?.user) {
        apiClient.setToken(session.access_token)
        
        const response = await apiClient.getProfile()
        if (response.success && response.data) {
          setUser(response.data)
        }
      } else if (event === 'SIGNED_OUT') {
        apiClient.setToken(null)
        setUser(null)
      }
    })

    return () => subscription.unsubscribe()
  }, [setUser, setLoading])

  if (!mounted) {
    return null
  }

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}
