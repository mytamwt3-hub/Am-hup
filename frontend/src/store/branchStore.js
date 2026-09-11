import { create } from 'zustand'

export const useBranchStore = create((set) => ({
  branches: [],
  loading: false,
  error: null,

  fetchBranches: async (token, tenantId) => {
    set({ loading: true, error: null })
    try {
      const response = await fetch('http://localhost:8000/api/v1/branches', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Tenant-ID': tenantId
        }
      })
      const data = await response.json()
      set({ branches: data })
    } catch (error) {
      set({ error: error.message })
    } finally {
      set({ loading: false })
    }
  },

  createBranch: async (token, tenantId, branchData) => {
    set({ loading: true, error: null })
    try {
      const response = await fetch('http://localhost:8000/api/v1/branches', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Tenant-ID': tenantId,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(branchData)
      })
      const data = await response.json()
      set((state) => ({ branches: [...state.branches, data] }))
      return true
    } catch (error) {
      set({ error: error.message })
      return false
    } finally {
      set({ loading: false })
    }
  }
}))
