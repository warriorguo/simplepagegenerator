import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import EditorPage from './pages/EditorPage'
import PublishedPage from './pages/PublishedPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/project/:id" element={<EditorPage />} />
        <Route path="/published/:id" element={<PublishedPage />} />
      </Routes>
    </BrowserRouter>
  )
}
