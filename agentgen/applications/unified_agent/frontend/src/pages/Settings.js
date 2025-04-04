import React, { useState, useEffect } from 'react';
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
  Switch,
  CircularProgress,
  Tabs,
  Tab,
  InputAdornment,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Check as CheckIcon
} from '@mui/icons-material';

function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function Settings() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [showPasswords, setShowPasswords] = useState({});
  
  const [slackSettings, setSlackSettings] = useState({
    bot_token: '',
    app_token: '',
    channel_id: '',
    user_id: ''
  });

  const [githubSettings, setGithubSettings] = useState({
    token: '',
    repo: '',
    webhook_secret: '',
    ngrok_auth_token: '',
    ngrok_domain: ''
  });

  const [aiSettings, setAiSettings] = useState({
    provider: 'anthropic',
    anthropic_api_key: '',
    openai_api_key: ''
  });

  const [appSettings, setAppSettings] = useState({
    data_dir: './data',
    docs_path: './docs',
    output_dir: './output',
    port: 8000,
    interval: 3600
  });

  const [workflowSettings, setWorkflowSettings] = useState({
    auto_start_requirements: false,
    auto_review_prs: true,
    auto_update_status: true
  });

  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success'
  });

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    setLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      setSlackSettings({
        bot_token: 'xoxb-sample-bot-token',
        app_token: 'xapp-sample-app-token',
        channel_id: 'C08K05KUL9G',
        user_id: 'U08K05UASCS'
      });
      
      setGithubSettings({
        token: 'github_pat_sample_token',
        repo: 'Zeeeepa/codegen',
        webhook_secret: 'webhook_secret_sample',
        ngrok_auth_token: 'ngrok_auth_token_sample',
        ngrok_domain: 'example.ngrok.io'
      });
      
      setAiSettings({
        provider: 'anthropic',
        anthropic_api_key: 'sk-ant-sample-key',
        openai_api_key: 'sk-sample-key'
      });
      
      setAppSettings({
        data_dir: './data',
        docs_path: './docs',
        output_dir: './output',
        port: 8000,
        interval: 3600
      });
      
      setWorkflowSettings({
        auto_start_requirements: false,
        auto_review_prs: true,
        auto_update_status: true
      });
      
      setLoading(false);
    }, 1000);
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleSlackChange = (e) => {
    const { name, value } = e.target;
    setSlackSettings({
      ...slackSettings,
      [name]: value
    });
  };

  const handleGithubChange = (e) => {
    const { name, value } = e.target;
    setGithubSettings({
      ...githubSettings,
      [name]: value
    });
  };

  const handleAiChange = (e) => {
    const { name, value } = e.target;
    setAiSettings({
      ...aiSettings,
      [name]: value
    });
  };

  const handleAppChange = (e) => {
    const { name, value } = e.target;
    setAppSettings({
      ...appSettings,
      [name]: name === 'port' || name === 'interval' ? Number(value) : value
    });
  };

  const handleWorkflowChange = (e) => {
    const { name, checked } = e.target;
    setWorkflowSettings({
      ...workflowSettings,
      [name]: checked
    });
  };

  const handleTogglePasswordVisibility = (field) => {
    setShowPasswords({
      ...showPasswords,
      [field]: !showPasswords[field]
    });
  };

  const handleSaveSettings = async () => {
    setSaving(true);
    
    // Simulate API call
    setTimeout(() => {
      setSnackbar({
        open: true,
        message: 'Settings saved successfully!',
        severity: 'success'
      });
      setSaving(false);
    }, 1000);
  };

  const handleTestSlackConnection = async () => {
    setLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      setSnackbar({
        open: true,
        message: 'Slack connection successful!',
        severity: 'success'
      });
      setLoading(false);
    }, 1000);
  };

  const handleCloseSnackbar = () => {
    setSnackbar({
      ...snackbar,
      open: false
    });
  };

  if (loading && !slackSettings.bot_token) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Settings
        </Typography>
        <Box>
          <Button 
            variant="outlined" 
            startIcon={<RefreshIcon />} 
            onClick={fetchSettings}
            disabled={loading || saving}
            sx={{ mr: 2 }}
          >
            Refresh
          </Button>
          <Button 
            variant="contained" 
            startIcon={<SaveIcon />} 
            onClick={handleSaveSettings}
            disabled={loading || saving}
          >
            {saving ? <CircularProgress size={24} /> : 'Save All Settings'}
          </Button>
        </Box>
      </Box>
      
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="settings tabs">
            <Tab label="Slack" />
            <Tab label="GitHub" />
            <Tab label="AI Providers" />
            <Tab label="Application" />
            <Tab label="Workflow" />
          </Tabs>
        </Box>
        
        {/* Slack Settings */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Slack Bot Token"
                name="bot_token"
                value={slackSettings.bot_token}
                onChange={handleSlackChange}
                margin="normal"
                type={showPasswords.bot_token ? 'text' : 'password'}
                helperText="Your Slack Bot Token (xoxb-...)"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => handleTogglePasswordVisibility('bot_token')}
                        edge="end"
                      >
                        {showPasswords.bot_token ? <VisibilityOffIcon /> : <VisibilityIcon />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Slack App Token"
                name="app_token"
                value={slackSettings.app_token}
                onChange={handleSlackChange}
                margin="normal"
                type={showPasswords.app_token ? 'text' : 'password'}
                helperText="Your Slack App Token (xapp-...)"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => handleTogglePasswordVisibility('app_token')}
                        edge="end"
                      >
                        {showPasswords.app_token ? <VisibilityOffIcon /> : <VisibilityIcon />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Default Channel ID"
                name="channel_id"
                value={slackSettings.channel_id}
                onChange={handleSlackChange}
                margin="normal"
                helperText="Default Slack channel ID (e.g., C08K05KUL9G)"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Codegen User ID"
                name="user_id"
                value={slackSettings.user_id}
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
                startIcon={<CheckIcon />}
                sx={{ mt: 2, mr: 2 }}
              >
                Test Connection
              </Button>
            </Grid>
          </Grid>
        </TabPanel>
        
        {/* GitHub Settings */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="GitHub Token"
                name="token"
                value={githubSettings.token}
                onChange={handleGithubChange}
                margin="normal"
                type={showPasswords.github_token ? 'text' : 'password'}
                helperText="Your GitHub Personal Access Token"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => handleTogglePasswordVisibility('github_token')}
                        edge="end"
                      >
                        {showPasswords.github_token ? <VisibilityOffIcon /> : <VisibilityIcon />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="GitHub Repository"
                name="repo"
                value={githubSettings.repo}
                onChange={handleGithubChange}
                margin="normal"
                helperText="Repository in format owner/repo"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Webhook Secret"
                name="webhook_secret"
                value={githubSettings.webhook_secret}
                onChange={handleGithubChange}
                margin="normal"
                type={showPasswords.webhook_secret ? 'text' : 'password'}
                helperText="Secret for GitHub webhooks"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => handleTogglePasswordVisibility('webhook_secret')}
                        edge="end"
                      >
                        {showPasswords.webhook_secret ? <VisibilityOffIcon /> : <VisibilityIcon />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Ngrok Auth Token"
                name="ngrok_auth_token"
                value={githubSettings.ngrok_auth_token}
                onChange={handleGithubChange}
                margin="normal"
                type={showPasswords.ngrok_auth_token ? 'text' : 'password'}
                helperText="Ngrok authentication token (for local development)"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => handleTogglePasswordVisibility('ngrok_auth_token')}
                        edge="end"
                      >
                        {showPasswords.ngrok_auth_token ? <VisibilityOffIcon /> : <VisibilityIcon />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Ngrok Domain"
                name="ngrok_domain"
                value={githubSettings.ngrok_domain}
                onChange={handleGithubChange}
                margin="normal"
                helperText="Ngrok domain (for local development)"
              />
            </Grid>
          </Grid>
        </TabPanel>
        
        {/* AI Settings */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                select
                fullWidth
                label="AI Provider"
                name="provider"
                value={aiSettings.provider}
                onChange={handleAiChange}
                margin="normal"
                SelectProps={{
                  native: true,
                }}
                helperText="Select your preferred AI provider"
              >
                <option value="anthropic">Anthropic</option>
                <option value="openai">OpenAI</option>
              </TextField>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Anthropic API Key"
                name="anthropic_api_key"
                value={aiSettings.anthropic_api_key}
                onChange={handleAiChange}
                margin="normal"
                type={showPasswords.anthropic_api_key ? 'text' : 'password'}
                helperText="Your Anthropic API Key"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => handleTogglePasswordVisibility('anthropic_api_key')}
                        edge="end"
                      >
                        {showPasswords.anthropic_api_key ? <VisibilityOffIcon /> : <VisibilityIcon />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="OpenAI API Key"
                name="openai_api_key"
                value={aiSettings.openai_api_key}
                onChange={handleAiChange}
                margin="normal"
                type={showPasswords.openai_api_key ? 'text' : 'password'}
                helperText="Your OpenAI API Key"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => handleTogglePasswordVisibility('openai_api_key')}
                        edge="end"
                      >
                        {showPasswords.openai_api_key ? <VisibilityOffIcon /> : <VisibilityIcon />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
          </Grid>
        </TabPanel>
        
        {/* Application Settings */}
        <TabPanel value={tabValue} index={3}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Data Directory"
                name="data_dir"
                value={appSettings.data_dir}
                onChange={handleAppChange}
                margin="normal"
                helperText="Directory for storing application data"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Documentation Path"
                name="docs_path"
                value={appSettings.docs_path}
                onChange={handleAppChange}
                margin="normal"
                helperText="Path to documentation files"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Output Directory"
                name="output_dir"
                value={appSettings.output_dir}
                onChange={handleAppChange}
                margin="normal"
                helperText="Directory for output files"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Port"
                name="port"
                type="number"
                value={appSettings.port}
                onChange={handleAppChange}
                margin="normal"
                helperText="Application port number"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Check Interval (seconds)"
                name="interval"
                type="number"
                value={appSettings.interval}
                onChange={handleAppChange}
                margin="normal"
                helperText="Interval for checking requirements in seconds"
              />
            </Grid>
          </Grid>
        </TabPanel>
        
        {/* Workflow Settings */}
        <TabPanel value={tabValue} index={4}>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={workflowSettings.auto_start_requirements}
                    onChange={handleWorkflowChange}
                    name="auto_start_requirements"
                    color="primary"
                  />
                }
                label="Automatically start processing requirements when they are added"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={workflowSettings.auto_review_prs}
                    onChange={handleWorkflowChange}
                    name="auto_review_prs"
                    color="primary"
                  />
                }
                label="Automatically review PRs when they are created or updated"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={workflowSettings.auto_update_status}
                    onChange={handleWorkflowChange}
                    name="auto_update_status"
                    color="primary"
                  />
                }
                label="Automatically update workflow status in real-time"
              />
            </Grid>
          </Grid>
        </TabPanel>
      </Card>

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