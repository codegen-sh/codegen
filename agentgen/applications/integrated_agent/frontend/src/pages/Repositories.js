import React from 'react';
import { Box, Typography } from '@mui/material';

function Repositories() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Repositories
      </Typography>
      <Typography variant="body1">
        This page will allow you to configure GitHub repositories for tracking and PR review.
      </Typography>
    </Box>
  );
}

export default Repositories;