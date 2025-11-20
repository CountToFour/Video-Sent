import React from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import { Box, Button } from "@mui/material";
import FeatureChart from "../components/FeatureChart.tsx";

const ResultPage: React.FC = () => {
    const location = useLocation()
    const navigate = useNavigate()

    const data = location.state

    if (!data) {
        return (
            <Box>
                <Typography variant="h6">Brak danych do wyświetlenia.</Typography>
                <Button variant="contained" onClick={() => navigate("/")}>
                    Powrót
                </Button>
            </Box>
        )
    }

    const overall = data.nlp_results?.overall

    return (
        <Paper sx={{ p: 4 }}>
            <Typography variant="h4" gutterBottom>
                Wyniki analizy
            </Typography>

            <Typography variant="h6" gutterBottom>
                {data.title}
            </Typography>

            {/* 🔥 NIEBIESKI OVERALL */}
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
                            backgroundColor: "#e3f2fd",       // jasny niebieski
                            borderLeft: "6px solid",
                            borderColor: "#1976d2",            // głęboki niebieski
                            color: "#0d47a1",                  // tekst ciemnoniebieski
                        }}
                    >
                        <Typography variant="h6">
                            {overall.label}
                        </Typography>

                        <Typography variant="body1">
                            Wynik: {overall.score.toFixed(3)}
                        </Typography>
                    </Paper>
                </>
            )}

            {/* 🔥 WYKRES */}
            <FeatureChart features={data.nlp_results?.features} />

        </Paper>
    )
}

export default ResultPage;
