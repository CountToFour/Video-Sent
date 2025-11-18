import axios from 'axios'
import type { AnalysisResult } from '../types'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api'
const client = axios.create({ baseURL: API_BASE })

export const submitVideo = async (url: string, platform: string) => {
  const res = await client.post('/downloader/videos/from_url/',
      {
          url: url,
          platform: platform
      }
  )
  return res.data
}

export const getJobStatus = async (jobId: string) => {
  const res = await client.get(`/jobs/${jobId}/`)
  return res.data
}

export const getAnalysis = async (id: string) => {
  const res = await client.get<AnalysisResult>(`/analyses/${id}/`)
  return res.data
}

export const listAnalyses = async () => {
  const res = await client.get<AnalysisResult[]>(`/analyses/`)
  return res.data
}
