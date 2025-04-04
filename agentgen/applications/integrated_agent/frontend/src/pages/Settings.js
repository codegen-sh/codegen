import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  TextField, 
  Button, 
  Card, 
  CardContent, 
  CardHeader, 
  Grid, 
  Divider,
  Snackbar,
  Alert,
  FormControlLabel,
  Switch
} from '@mui/material';

function Settings() {
  const [slackSettings, setSlackSettings] = useState({
    botToken: '',
    appToken: '',
    channel: '',
    codegenUserId: ''
  });

  const [githubSettings, setGithubSettings] = useState({
    token: ''
  });

  const [aiSettings, setAiSettings] = useState({
    provider: 'anthropic',
    anthropicKey: '',
    openaiKey: ''
  });

  const [generalSettings, setGeneralSettings] = useState({
    autoStartRequirements: false,
    autoReviewPRs: true
  });

  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success'
  });

  const handleSlackChange = (e) => {
    setSlackSettings({
      ...slackSettings,
      [e.target.name]: e.target.value
    });
  };

  const handleGithubChange = (e) => {
    setGithubSettings({
      ...githubSettings,
      [e.target.name]: e.target.value
    });
  };

  const handleAiChange = (e) => {
    setAiSettings({
      ...aiSettings,
      [e.target.name]: e.target.value
    });
  };

  const handleGeneralChange = (e) => {
    setGeneralSettings({
      ...generalSettings,
      [e.target.name]: e.target.checked
    });
  };

  const handleSaveSettings = () => {
    // TODO: Implement API call to save settings
    setSnackbar({
      open: true,
      message: 'Settings saved successfully!',
      severity: 'success'
    });
  };

  const handleTestSlackConnection = () => {
    // TODO: Implement API call to test Slack connection
    setSnackbar({
      open: true,
      message: 'Slack connection successful!',
      severity: 'success'
    });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({
      ...snackbar,
      open: false
    });
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>
      
      <Grid container spacing={3}>
        {/* Slack Integration Settings */}
        <Grid item xs={12}>
          <Card>
            <CardHeader title="Slack Integration" />
            <Divider />
            <CardContent>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Slack Bot Token"
                    name="botToken"
                    value={slackSettings.botToken}
                    onChange={handleSlackChange}
                    margin="normal"
                    type="password"
                    helperText="Your Slack Bot Token (xoxb-...)"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Slack App Token"
                    name="appToken"
                    value={slackSettings.appToken}
                    onChange={handleSlackChange}
                    margin="normal"
                    type="password"
                    helperText="Your Slack App Token (xapp-...)"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Default Channel ID"
                    name="channel"
                    value={slackSettings.channel}
                    onChange={handleSlackChange}
                    margin="normal"
                    helperText="Default Slack channel ID (e.g., C08K05KUL9G)"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Codegen User ID"
                    name="codegenUserId"
                    value={slackSettings.codegenUserId}
                    onChange={handleSlackChange}
                    margin="normal"
                    helperText="Slack User ID for Codegen"
                  />
                </Grid>
                <Grid item xs={12}>
                  <Button 
                    variant="contained" 
                    color="primary" 
                    onClick={handleTestSlackConnection}
                    sx={{ mt: 2, mr: 2 }}
                  >
                    Test Connection
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* GitHub Settings */}
        <Grid item xs={12}>
          <Card>
            <CardHeader title="GitHub Integration" />
            <Divider />
            <CardContent>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="GitHub Token"
                    name="token"
                    value={githubSettings.token}
                    onChange={handleGithubChange}
                    margin="normal"
                    type="password"
                    helperText="Your GitHub Personal Access Token"
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* AI Settings */}
        <Grid item xs={12}>
          <Card>
            <CardHeader title="AI Integration" />
            <Divider />
            <CardContent>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Anthropic API Key"
                    name="anthropicKey"
                    value={aiSettings.anthropicKey}
                    onChange={handleAiChange}
                    margin="normal"
                    type="password"
                    helperText="Your Anthropic API Key"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="OpenAI API Key"
                    name="openaiKey"
                    value={aiSettings.openaiKey}
                    onChange={handleAiChange}
                    margin="normal"
                    type="password"
                    helperText="Your OpenAI API Key"
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* General Settings */}
        <Grid item xs={12}>
          <Card>
            <CardHeader title="General Settings" />
            <Divider />
            <CardContent>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={generalSettings.autoStartRequirements}
                        onChange={handleGeneralChange}
                        name="autoStartRequirements"
                        color="primary"
                      />
                    }
                    label="Automatically start sending requirements when a new project is created"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={generalSettings.autoReviewPRs}
                        onChange={handleGeneralChange}
                        name="autoReviewPRs"
                        color="primary"
                      />
                    }
                    label="Automatically review PRs when they are created or updated"
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Save Button */}
        <Grid item xs={12}>
          <Button 
            variant="contained" 
            color="primary" 
            onClick={handleSaveSettings}
            sx={{ mt: 2 }}
          >
            Save Settings
          </Button>
        </Grid>
      </Grid>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default Settings;