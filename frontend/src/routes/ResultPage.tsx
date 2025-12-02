import React from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import { Box, Button, LinearProgress } from '@mui/material'
import FeatureChart from '../components/FeatureChart.tsx'

const ResultPage: React.FC = () => {
    const location = useLocation()
    const navigate = useNavigate()

    const data = location.state as any

    if (!data) {
        return (
            <Box sx={{ p: 4 }}>
                <Typography variant="h6" gutterBottom>
                    Brak danych do wyświetlenia.
                </Typography>
                <Button variant="contained" onClick={() => navigate('/')}>
                    Powrót
                </Button>
            </Box>
        )
    }

    const overall = data.nlp_results?.overall
    const summary: string | undefined = data.nlp_results?.user_summary ?? undefined

    return (
        <Paper sx={{ p: 4 }}>
            <Typography variant="h4" gutterBottom>
                Wyniki analizy
            </Typography>

            <Typography variant="h6" gutterBottom>
                {data.title}
            </Typography>

            {/* 🔵 OCENA OGÓLNA + TERMOMETR */}
            {overall && (
                <>
                    <Typography variant="h5" sx={{ mt: 3 }}>
                        Ocena ogólna
                    </Typography>

                    <Paper
                        elevation={3}
                        sx={{
                            p: 2,
                            mt: 1,
                            mb: 3,
                            backgroundColor: '#e3f2fd',
                            borderLeft: '6px solid',
                            borderColor: '#1976d2',
                            color: '#0d47a1',
                        }}
                    >
                        <Typography variant="h6">
                            {overall.label}
                        </Typography>

                        <Typography variant="body1" sx={{ mb: 1 }}>
                            Wynik: {overall.score.toFixed(3)}
                        </Typography>

                        {/* 👉 termometr (0–100%) */}
                        <Box sx={{ mt: 1 }}>
                            <LinearProgress
                                variant="determinate"
                                value={overall.score * 100}
                                sx={{ height: 10, borderRadius: 5 }}
                            />
                            <Typography variant="caption">
                                0 = bardzo negatywnie, 1 = bardzo pozytywnie
                            </Typography>
                        </Box>
                    </Paper>
                </>
            )}

            {/* 🟠 PODSUMOWANIE Z GROQA – jeśli jest */}
            {summary && (
                <Paper
                    elevation={1}
                    sx={{
                        p: 2,
                        mb: 3,
                        backgroundColor: '#1a8eed',
                    }}
                >
                    <Typography variant="h6" gutterBottom>
                        Podsumowanie w prostym języku
                    </Typography>
                    <Typography variant="body1">
                        {summary}
                    </Typography>
                </Paper>
            )}

            {/* 🔥 WYKRES CECH */}
            <FeatureChart features={data.nlp_results?.features} />
        </Paper>
    )
}

export default ResultPage
