import React, { useState } from 'react'
import { Box, TextField, Button, MenuItem, Paper, Typography, Alert } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { submitVideo } from '../services/api'

export default function Home() {
  const [url, setUrl] = useState('')
  const [platform, setPlatform] = useState<'youtube'|'tiktok'|'instagram'>('youtube')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!url) return setError('Wklej link do wideo')
    try {
      setLoading(true)
      const res = await submitVideo(url, platform)
      navigate(`/results/${res.jobId}`)
    } catch (err: any) {
      setError(err?.response?.data?.message || err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Paper sx={{ p: 4, maxWidth: 800, mx: 'auto', mt: 4 }}>
      <Typography variant="h5" gutterBottom>Analiza recenzji wideo</Typography>
      <Box component="form" onSubmit={handleSubmit} sx={{ display: 'grid', gap: 2 }}>
        {error && <Alert severity="error">{error}</Alert>}
        <TextField label="Link do wideo" value={url} onChange={(e) => setUrl(e.target.value)} fullWidth />
        <TextField select label="Platforma" value={platform} onChange={(e) => setPlatform(e.target.value as any)}>
          <MenuItem value="youtube">YouTube</MenuItem>
          <MenuItem value="tiktok">TikTok</MenuItem>
          <MenuItem value="instagram">Instagram</MenuItem>
        </TextField>
        <Button variant="contained" type="submit" disabled={loading}>{loading ? 'Wysyłanie...' : 'Analizuj wideo'}</Button>
        <Typography variant="body2" color="text.secondary">Po wysłaniu backend pobierze wideo/transkrypcję i przeprowadzi analizę. Strona wyników będzie sprawdzać status zadania.</Typography>
      </Box>
    </Paper>
  )
}
