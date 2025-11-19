import React, {useContext} from 'react'
import AppBar from '@mui/material/AppBar'
import Toolbar from '@mui/material/Toolbar'
import Typography from '@mui/material/Typography'
import {Button, IconButton, useTheme} from '@mui/material'
import { Link as RouterLink } from 'react-router-dom'
import {ColorModeContext} from "../../context/CustomeThemeProvider.tsx";
import LightModeIcon from "@mui/icons-material/LightMode";
import DarkModeIcon from "@mui/icons-material/DarkMode";

export default function Navbar() {
    const theme = useTheme();
    const { toggleColorMode } = useContext(ColorModeContext);

  return (
    <AppBar position="static">
      <Toolbar style={{ display: "flex", justifyContent: "space-between" }}>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Video Sentiment Analyzer
        </Typography>
          <IconButton color="inherit" onClick={toggleColorMode}>
              {theme.palette.mode === "dark" ? <LightModeIcon /> : <DarkModeIcon />}
          </IconButton>
        <Button color="inherit" component={RouterLink} to="/">Home</Button>
      </Toolbar>
    </AppBar>
  )
}