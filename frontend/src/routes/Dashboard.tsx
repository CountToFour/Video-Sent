import React, { useEffect, useState } from 'react'
import { listAnalyses } from '../services/api'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemText from '@mui/material/ListItemText'
import { Link as RouterLink } from 'react-router-dom'

export default function Dashboard() {
  const [items, setItems] = useState<any[]>([])

  useEffect(() => {
    listAnalyses().then(setItems).catch(console.error)
  }, [])

  return (
    <Paper sx={{ p: 4 }}>
      <Typography variant="h5">Dashboard</Typography>
      {items.length === 0 ? (
        <Typography sx={{ mt: 2 }}>Brak analiz — dodaj wideo na stronie głównej.</Typography>
      ) : (
        <List>
          {items.map(it => (
            <ListItem key={it.id} secondaryAction={<RouterLink to={`/results/${it.id}`}>Szczegóły</RouterLink>}>
              <ListItemText primary={it.url} secondary={`Overall: ${it.overall.sentiment} (${it.overall.score.toFixed(2)}) — ${new Date(it.createdAt).toLocaleString()}`} />
            </ListItem>
          ))}
        </List>
      )}
    </Paper>
  )
}