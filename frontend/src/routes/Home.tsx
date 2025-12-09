import React, { useState } from 'react'
import {Box, TextField, Button, Paper, Typography, Alert, LinearProgress} from '@mui/material'
import { useNavigate } from 'react-router-dom'
import {analyzeVideo} from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

export default function Home() {
    const [url, setUrl] = useState('')
    const [loading, setLoading] = useState(false)
    const [progressMsg, setProgressMsg] = useState<string>('')
    const [progressValue, setProgressValue] = useState(0)
    const [error, setError] = useState<string | null>(null)
    const navigate = useNavigate()

    const isValidYouTubeURL = (link: string) => {
        const regex =
            /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/).+/
        return regex.test(link)
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError(null)
        setLoading(true)
        setProgressValue(0)
        setProgressMsg('Inicjalizacja...')

        if (!url) {
            setLoading(false)
            return setError('Wklej link do wideo')
        }

        if (!isValidYouTubeURL(url)) {
            setLoading(false)
            return setError('Podaj prawidłowy link do YouTube')
        }

        try {
            const res = await analyzeVideo(url, (msg, progress) => {
                setProgressMsg(msg);
                setProgressValue(progress);
            });

            if (
                !res.nlp_results ||
                !Array.isArray(res.nlp_results.features) ||
                res.nlp_results.features.length < 3
            ) {
                setError("Nie udało się przetworzyć wideo. Upewnij się, że podany link prowadzi do poprawnego filmu YouTube.")
                return
            }

            navigate("/results", { state: res })
        } catch (err: any) {
            setError(err.message || "Błąd analizy")
        } finally {
            setLoading(false)
            setProgressMsg('')
            setProgressValue(0)
        }
    }

    return (
        <Paper sx={{ p: 4, maxWidth: 800, mx: 'auto', mt: 4 }}>
            <Typography variant="h5" gutterBottom>
                Analiza recenzji wideo z platformy YouTube
            </Typography>

            <Box component="form" onSubmit={handleSubmit} sx={{ display: 'grid', gap: 2 }}>
                {error && <Alert severity="error">{error}</Alert>}

                <TextField
                    label="Link do wideo"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    fullWidth
                    disabled={loading}
                />

                <Button variant="contained" type="submit" disabled={loading}>
                    {loading ? 'Przetwarzanie...' : 'Analizuj wideo'}
                </Button>

                {loading && (
                    <Box sx={{ mt: 3 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography variant="body2" color="primary" sx={{ fontWeight: 'bold' }}>
                                {progressMsg}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                                {progressValue}%
                            </Typography>
                        </Box>

                        <LinearProgress
                            variant="determinate"
                            value={progressValue}
                            sx={{ height: 10, borderRadius: 5 }}
                        />
                        <LoadingSpinner />
                    </Box>
                )}
            </Box>
        </Paper>
    )
}