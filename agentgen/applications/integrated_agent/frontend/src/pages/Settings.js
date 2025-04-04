import React from 'react';
import { Box, Typography } from '@mui/material';

function Settings() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>
      <Typography variant="body1">
        This page will allow you to configure application settings, API keys, and Slack integration.
      </Typography>
    </Box>
  );
}

export default Settings;