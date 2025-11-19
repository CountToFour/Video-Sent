import React, { useEffect, useState } from 'react'
import {useLocation, useNavigate, useParams} from 'react-router-dom'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import type { Video } from '../types'
import {Box, Button} from "@mui/material";
import FeatureChart from "../components/FeatureChart.tsx";

const ResultPage: React.FC = () => {
    const location = useLocation()
    const navigate = useNavigate()

    const data = location.state as Video | undefined

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

    return (
        <Paper sx={{ p: 4 }}>
            <Typography variant="h4" gutterBottom>
                Wyniki analizy
            </Typography>

            <Typography variant="h6" gutterBottom>
                {data.title}
            </Typography>

            {/* Wykres */}
            <FeatureChart features={data.features} />
        </Paper>
    )
}

export default ResultPage;
