import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import CssBaseline from '@mui/material/CssBaseline'
import CustomThemeProvider from "./context/CustomeThemeProvider.tsx";

createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <CustomThemeProvider>
            <CssBaseline />
            <BrowserRouter>
                <App />
            </BrowserRouter>
        </CustomThemeProvider>
    </React.StrictMode>
)