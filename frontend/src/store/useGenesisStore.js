import { create } from 'zustand'
import client from '@/api/client'

const useGenesisStore = create((set) => ({
    inspiration: "",
    setInspiration: (val) => set({ inspiration: val }),

    proposals: [],
    isLoadingProposals: false,
    error: null,

    selectedProposal: null,
    setSelectedProposal: (proposal) => set({ selectedProposal: proposal }),

    isInitializing: false,

    generateProposals: async (inspiration) => {
        set({ isLoadingProposals: true, error: null })
        try {
            const { data } = await client.post('/genesis/propose', { inspiration })
            set({ proposals: data.proposals || [], isLoadingProposals: false })
        } catch (err) {
            set({ error: err.response?.data?.error || err.message, isLoadingProposals: false })
        }
    },

    initializeProject: async (project_name, config_yaml) => {
        set({ isInitializing: true, error: null })
        try {
            await client.post('/genesis/init', { project_name, config_yaml })
            set({ isInitializing: false })
            return true
        } catch (err) {
            set({ error: err.response?.data?.error || err.message, isInitializing: false })
            return false
        }
    }
}))

export default useGenesisStore
