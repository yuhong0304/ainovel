import { create } from 'zustand'
import client from '@/api/client'

const useProjectStore = create((set, get) => ({
    projects: [],
    currentProject: null,
    isLoading: false,
    error: null,

    // Fetch list of all projects
    fetchProjects: async () => {
        set({ isLoading: true, error: null })
        try {
            const { data } = await client.get('/api/projects')
            // Backend returns a list directly
            const projectList = Array.isArray(data) ? data : (data.projects || [])
            set({ projects: projectList, isLoading: false })
        } catch (err) {
            set({ error: err.message, isLoading: false })
        }
    },

    // Load specific project details
    loadProject: async (name) => {
        set({ isLoading: true, error: null })
        try {
            // First ensure we have the list
            if (get().projects.length === 0) {
                await get().fetchProjects()
            }

            const project = get().projects.find(p => p.name === name)
            if (project) {
                set({ currentProject: project, isLoading: false })
                return project
            } else {
                // If not in list (maybe new), try to fetch individually if API supports or re-fetch list
                await get().fetchProjects()
                const retry = get().projects.find(p => p.name === name)
                if (retry) {
                    set({ currentProject: retry, isLoading: false })
                    return retry
                }
                throw new Error("Project not found")
            }
        } catch (err) {
            set({ error: err.message, isLoading: false })
            return null
        }
    },

    setCurrentProject: (project) => set({ currentProject: project })
}))

export default useProjectStore
