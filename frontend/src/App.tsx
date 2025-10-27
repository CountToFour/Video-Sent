import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Navbar from './components/layout/Navbar'
import Home from './routes/Home'
import Dashboard from './routes/Dashboard'
import ResultPage from './routes/ResultPage'


export default function App() {
  return (
    <div>
      <Navbar />
      <main style={{ padding: 24 }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/results/:id" element={<ResultPage />} />
        </Routes>
      </main>
    </div>
  )
}