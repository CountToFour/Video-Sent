import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { getJobStatus, getAnalysis } from '../services/api'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import LoadingSpinner from '../components/LoadingSpinner'
import AnalysisChart from '../components/AnalysisChart'
import FeatureCard from '../components/FeatureCard'

export default function ResultPage() {
  const { id } = useParams()
  const [job, setJob] = useState<any>(null)
  const [analysis, setAnalysis] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    let cancelled = false

    const poll = async () => {
      try {
        const status = await getJobStatus(id)
        if (cancelled) return
        setJob(status)
        if (status.state === 'finished' && status.analysisId) {
          const data = await getAnalysis(status.analysisId)
          setAnalysis(data)
        }
        if (status.state === 'failed') setError(status.error || 'Analiza nie powiodła się')
      } catch (e: any) {
        setError(e?.message || 'Błąd')
      }
    }

    poll()
    const iv = setInterval(poll, 3000)
    return () => { cancelled = true; clearInterval(iv) }
  }, [id])

  if (error) return <Paper sx={{ p: 4 }}><Typography color="error">{error}</Typography></Paper>
  if (!analysis) return <Paper sx={{ p: 4 }}><Typography variant="h6">Status zadania</Typography><pre>{JSON.stringify(job, null, 2)}</pre><LoadingSpinner /></Paper>

  return (
    <Paper sx={{ p: 4 }}>
      <Typography variant="h5">Wynik analizy</Typography>
      <Typography variant="subtitle1">Ogólna ocena: {analysis.overall.sentiment} ({analysis.overall.score.toFixed(2)})</Typography>
      <Typography variant="body2">URL: <a href={analysis.url} target="_blank">Otwórz</a></Typography>

      <div style={{ marginTop: 20 }}>
        <AnalysisChart features={analysis.features} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 12, marginTop: 20 }}>
        {analysis.features.map((f: any) => (
          <FeatureCard key={f.feature} feature={f.feature} sentiment={f.sentiment} score={f.score} examples={f.examples} />
        ))}
      </div>
    </Paper>
  )
}