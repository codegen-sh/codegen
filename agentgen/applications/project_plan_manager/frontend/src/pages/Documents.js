import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

function Documents() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Documents
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1">
          Document management functionality will be implemented here.
        </Typography>
      </Paper>
    </Box>
  );
}

export default Documents;