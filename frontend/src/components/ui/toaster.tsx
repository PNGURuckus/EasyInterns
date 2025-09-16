"use client"

import { useEffect, useState } from "react"
import { useTheme } from "next-themes"
import { Toast, ToastProvider, ToastViewport } from "@/components/ui/toast"

export function Toaster() {
  const [mounted, setMounted] = useState(false)
  const { theme } = useTheme()

  // Only render on client
  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) return null

  return (
    <ToastProvider>
      <ToastViewport />
    </ToastProvider>
  )
}
