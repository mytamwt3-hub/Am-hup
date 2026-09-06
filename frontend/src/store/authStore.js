import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useAuthStore = create(
  persist(
    (set) => ({
      token: null,
      user: null,
      tenantId: null,
      loading: false,
      error: null,

      login: async (email, password) => {
        set({ loading: true, error: null })
        try {
          const response = await fetch('http://localhost:8000/api/v1/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
          })
          const data = await response.json()
          if (response.ok) {
            set({ token: data.access_token, user: { email: data.user_email }, tenantId: data.tenant_id })
            return true
          } else {
            set({ error: data.detail || 'Login failed' })
            return false
          }
        } catch (error) {
          set({ error: error.message })
          return false
        } finally {
          set({ loading: false })
        }
      },

      register: async (formData) => {
        set({ loading: true, error: null })
        try {
          const response = await fetch('http://localhost:8000/api/v1/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
          })
          const data = await response.json()
          if (response.ok) {
            set({ token: data.access_token, user: { email: data.user_email }, tenantId: data.tenant_id })
            return true
          } else {
            set({ error: data.detail || 'Registration failed' })
            return false
          }
        } catch (error) {
          set({ error: error.message })
          return false
        } finally {
          set({ loading: false })
        }
      },

      logout: () => set({ token: null, user: null, tenantId: null, error: null })
    }),
    { name: 'auth-store' }
  )
)
