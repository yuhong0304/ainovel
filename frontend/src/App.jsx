import { Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'sonner'
import Home from '@/components/Home'
import Wizard from '@/components/Wizard'
import ProjectLayout from '@/components/layout/ProjectLayout'
import Dashboard from '@/components/modules/Dashboard'
import WritingStudio from '@/components/modules/WritingStudio'
import Worldbook from '@/components/modules/Worldbook'
import Settings from '@/components/modules/Settings'
import Export from '@/components/modules/Export'
import BatchGenerate from '@/components/modules/BatchGenerate'
import Statistics from '@/components/modules/Statistics'

function App() {
  return (
    <div className="dark min-h-screen bg-background text-foreground font-sans antialiased">
      <Toaster
        position="bottom-right"
        toastOptions={{
          className: 'bg-card border-border text-foreground',
        }}
      />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/create" element={<Wizard />} />

        <Route path="/project/:projectId" element={<ProjectLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="write" element={<WritingStudio />} />
          <Route path="world" element={<Worldbook />} />
          <Route path="export" element={<Export />} />
          <Route path="batch" element={<BatchGenerate />} />
          <Route path="stats" element={<Statistics />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </div>
  )
}

export default App



