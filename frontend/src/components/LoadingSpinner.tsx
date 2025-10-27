import React from 'react'
import CircularProgress from '@mui/material/CircularProgress'
import Box from '@mui/material/Box'

export default function LoadingSpinner() {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
      <CircularProgress />
    </Box>
  )
}