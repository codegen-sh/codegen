import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

function Requirements() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Requirements
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1">
          Requirements tracking functionality will be implemented here.
        </Typography>
      </Paper>
    </Box>
  );
}

export default Requirements;