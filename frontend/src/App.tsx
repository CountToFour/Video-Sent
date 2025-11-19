import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Navbar from './components/layout/Navbar'
import Home from './routes/Home'
import ResultPage from './routes/ResultPage'


export default function App() {
  return (
    <div>
      <Navbar />
      <main style={{ padding: 24 }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/results" element={<ResultPage />} />
        </Routes>
      </main>
    </div>
  )
}