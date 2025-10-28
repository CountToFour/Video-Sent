import React from 'react'
import AppBar from '@mui/material/AppBar'
import Toolbar from '@mui/material/Toolbar'
import Typography from '@mui/material/Typography'
import { Button } from '@mui/material'
import { Link as RouterLink } from 'react-router-dom'

export default function Navbar() {
  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Video Sentiment Analyzer
        </Typography>
        <Button color="inherit" component={RouterLink} to="/">Home</Button>
        {/* <Button color="inherit" component={RouterLink} to="/dashboard">Dashboard</Button> */}
      </Toolbar>
    </AppBar>
  )
}