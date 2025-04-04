import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

function ProjectPlans() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Project Plans
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1">
          Project planning functionality will be implemented here.
        </Typography>
      </Paper>
    </Box>
  );
}

export default ProjectPlans;