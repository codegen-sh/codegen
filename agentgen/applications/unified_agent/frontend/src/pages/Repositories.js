import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

function Repositories() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Repositories
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1">
          Repository management functionality will be implemented here.
        </Typography>
      </Paper>
    </Box>
  );
}

export default Repositories;