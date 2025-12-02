import React, { useState } from 'react'
import { Box, TextField, Button, Paper, Typography, Alert } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { submitVideo } from '../services/api'

export default function Home() {
    const [url, setUrl] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const navigate = useNavigate()

    // Walidacja linku YouTube
    const isValidYouTubeURL = (link: string) => {
        const regex =
            /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/).+/
        return regex.test(link)
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError(null)

        if (!url) {
            return setError('Wklej link do wideo')
        }

        if (!isValidYouTubeURL(url)) {
            return setError('Podaj prawidłowy link do YouTube')
        }

        try {
            setLoading(true)
            const res = await submitVideo(url, "youtube")  // platforma na stałe
            console.log(res)
            if (
                !res ||
                !res.nlp_results ||
                !Array.isArray(res.nlp_results.features) ||
                res.nlp_results.features.length < 3
            ) {
                setError("Nie udało się przetworzyć wideo. Upewnij się, że podany link prowadzi do poprawnego filmu YouTube.")
                return
            }

            navigate("/results", { state: res })
        } catch (err: any) {
            setError(err?.response?.data?.message || err.message)
        } finally {
            setLoading(false)
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
                />

                {/* Usunięto pole wyboru platformy */}

                <Button variant="contained" type="submit" disabled={loading}>
                    {loading ? 'Wysyłanie...' : 'Analizuj wideo'}
                </Button>

                <Typography variant="body2" color="text.secondary">
                    Po wysłaniu backend pobierze wideo/transkrypcję i przeprowadzi analizę.
                </Typography>
            </Box>
        </Paper>
    )
}
