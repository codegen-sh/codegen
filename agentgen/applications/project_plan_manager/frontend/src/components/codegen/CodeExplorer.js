import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  TextField, 
  Button, 
  Grid, 
  Card, 
  CardContent, 
  CardActions,
  Divider,
  List,
  ListItem,
  ListItemText,
  Paper,
  CircularProgress,
  Alert,
  Snackbar,
  Tabs,
  Tab,
  IconButton,
  Tooltip
} from '@mui/material';
import { 
  Search as SearchIcon, 
  Code as CodeIcon,
  GitHub as GitHubIcon,
  ContentCopy as CopyIcon,
  Refresh as RefreshIcon,
  Create as CreateIcon
} from '@mui/icons-material';
import axios from 'axios';

function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`codegen-tabpanel-${index}`}
      aria-labelledby={`codegen-tab-${index}`}
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

function CodeExplorer() {
  const [activeTab, setActiveTab] = useState(0);
  const [repoName, setRepoName] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileContent, setFileContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'info'
  });
  
  // PR creation state
  const [prTitle, setPrTitle] = useState('');
  const [prBody, setPrBody] = useState('');
  const [baseBranch, setBaseBranch] = useState('main');
  const [headBranch, setHeadBranch] = useState('');
  const [prResult, setPrResult] = useState(null);
  
  // PR details state
  const [prNumber, setPrNumber] = useState('');
  const [prDetails, setPrDetails] = useState(null);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleSearch = async () => {
    if (!repoName || !searchQuery) {
      setSnackbar({
        open: true,
        message: 'Please enter a repository name and search query',
        severity: 'warning'
      });
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('/api/codegen/search', {
        repo_name: repoName,
        query: searchQuery
      });
      
      setSearchResults(response.data);
      
      if (response.data.length === 0) {
        setSnackbar({
          open: true,
          message: 'No results found',
          severity: 'info'
        });
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Error searching code');
      setSnackbar({
        open: true,
        message: err.response?.data?.detail || 'Error searching code',
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = async (filePath) => {
    if (!repoName || !filePath) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('/api/codegen/file', {
        repo_name: repoName,
        file_path: filePath
      });
      
      setSelectedFile(filePath);
      setFileContent(response.data.content);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error getting file content');
      setSnackbar({
        open: true,
        message: err.response?.data?.detail || 'Error getting file content',
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePR = async () => {
    if (!repoName || !prTitle || !prBody) {
      setSnackbar({
        open: true,
        message: 'Please enter a repository name, PR title, and PR body',
        severity: 'warning'
      });
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('/api/codegen/pr/create', {
        repo_name: repoName,
        title: prTitle,
        body: prBody,
        base_branch: baseBranch,
        head_branch: headBranch || undefined
      });
      
      setPrResult(response.data);
      setSnackbar({
        open: true,
        message: `PR #${response.data.pr_number} created successfully`,
        severity: 'success'
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Error creating PR');
      setSnackbar({
        open: true,
        message: err.response?.data?.detail || 'Error creating PR',
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleGetPRDetails = async () => {
    if (!repoName || !prNumber) {
      setSnackbar({
        open: true,
        message: 'Please enter a repository name and PR number',
        severity: 'warning'
      });
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('/api/codegen/pr/details', {
        repo_name: repoName,
        pr_number: parseInt(prNumber)
      });
      
      setPrDetails(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error getting PR details');
      setSnackbar({
        open: true,
        message: err.response?.data?.detail || 'Error getting PR details',
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCopyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setSnackbar({
      open: true,
      message: 'Copied to clipboard',
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
    <Box sx={{ width: '100%' }}>
      <Typography variant="h4" gutterBottom>
        <CodeIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
        Code Explorer
      </Typography>
      
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          variant="fullWidth"
        >
          <Tab label="Code Search" icon={<SearchIcon />} />
          <Tab label="PR Management" icon={<GitHubIcon />} />
        </Tabs>
      </Paper>
      
      <TabPanel value={activeTab} index={0}>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Search Code
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={4}>
                    <TextField
                      fullWidth
                      label="Repository Name"
                      placeholder="owner/repo"
                      value={repoName}
                      onChange={(e) => setRepoName(e.target.value)}
                      margin="normal"
                      variant="outlined"
                      helperText="Format: owner/repo (e.g., octocat/Hello-World)"
                    />
                  </Grid>
                  <Grid item xs={12} md={8}>
                    <TextField
                      fullWidth
                      label="Search Query"
                      placeholder="Enter search query"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      margin="normal"
                      variant="outlined"
                    />
                  </Grid>
                </Grid>
              </CardContent>
              <CardActions>
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<SearchIcon />}
                  onClick={handleSearch}
                  disabled={loading}
                >
                  {loading ? 'Searching...' : 'Search'}
                </Button>
              </CardActions>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card sx={{ height: '100%', maxHeight: 600, overflow: 'auto' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Search Results
                </Typography>
                {loading && (
                  <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
                    <CircularProgress />
                  </Box>
                )}
                {error && (
                  <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                  </Alert>
                )}
                {searchResults.length > 0 ? (
                  <List>
                    {searchResults.map((result, index) => (
                      <React.Fragment key={index}>
                        <ListItem
                          button
                          onClick={() => handleFileSelect(result.file_path)}
                          selected={selectedFile === result.file_path}
                        >
                          <ListItemText
                            primary={result.file_path}
                            secondary={`Line ${result.line_number}: ${result.line}`}
                          />
                        </ListItem>
                        {index < searchResults.length - 1 && <Divider />}
                      </React.Fragment>
                    ))}
                  </List>
                ) : (
                  <Typography variant="body2" color="textSecondary" align="center">
                    No results to display
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={8}>
            <Card sx={{ height: '100%', maxHeight: 600, overflow: 'auto' }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">
                    {selectedFile ? `File: ${selectedFile}` : 'File Content'}
                  </Typography>
                  {selectedFile && (
                    <Tooltip title="Copy to clipboard">
                      <IconButton onClick={() => handleCopyToClipboard(fileContent)}>
                        <CopyIcon />
                      </IconButton>
                    </Tooltip>
                  )}
                </Box>
                {loading && (
                  <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
                    <CircularProgress />
                  </Box>
                )}
                {selectedFile ? (
                  <Paper
                    sx={{
                      p: 2,
                      backgroundColor: '#f5f5f5',
                      fontFamily: 'monospace',
                      whiteSpace: 'pre-wrap',
                      overflowX: 'auto'
                    }}
                  >
                    {fileContent}
                  </Paper>
                ) : (
                  <Typography variant="body2" color="textSecondary" align="center">
                    Select a file to view its content
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>
      
      <TabPanel value={activeTab} index={1}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Create Pull Request
                </Typography>
                <TextField
                  fullWidth
                  label="Repository Name"
                  placeholder="owner/repo"
                  value={repoName}
                  onChange={(e) => setRepoName(e.target.value)}
                  margin="normal"
                  variant="outlined"
                  helperText="Format: owner/repo (e.g., octocat/Hello-World)"
                />
                <TextField
                  fullWidth
                  label="PR Title"
                  placeholder="Enter PR title"
                  value={prTitle}
                  onChange={(e) => setPrTitle(e.target.value)}
                  margin="normal"
                  variant="outlined"
                />
                <TextField
                  fullWidth
                  label="PR Body"
                  placeholder="Enter PR description"
                  value={prBody}
                  onChange={(e) => setPrBody(e.target.value)}
                  margin="normal"
                  variant="outlined"
                  multiline
                  rows={4}
                />
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Base Branch"
                      placeholder="main"
                      value={baseBranch}
                      onChange={(e) => setBaseBranch(e.target.value)}
                      margin="normal"
                      variant="outlined"
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Head Branch (optional)"
                      placeholder="feature-branch"
                      value={headBranch}
                      onChange={(e) => setHeadBranch(e.target.value)}
                      margin="normal"
                      variant="outlined"
                      helperText="Leave empty to create a new branch"
                    />
                  </Grid>
                </Grid>
              </CardContent>
              <CardActions>
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<CreateIcon />}
                  onClick={handleCreatePR}
                  disabled={loading}
                >
                  {loading ? 'Creating...' : 'Create PR'}
                </Button>
              </CardActions>
            </Card>
            
            {prResult && (
              <Card sx={{ mt: 2 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    PR Created Successfully
                  </Typography>
                  <Typography variant="body1">
                    <strong>PR Number:</strong> {prResult.pr_number}
                  </Typography>
                  <Typography variant="body1">
                    <strong>Title:</strong> {prResult.title}
                  </Typography>
                  <Typography variant="body1">
                    <strong>State:</strong> {prResult.state}
                  </Typography>
                  <Button
                    variant="outlined"
                    color="primary"
                    href={prResult.pr_url}
                    target="_blank"
                    sx={{ mt: 2 }}
                  >
                    View on GitHub
                  </Button>
                </CardContent>
              </Card>
            )}
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Get PR Details
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={8}>
                    <TextField
                      fullWidth
                      label="Repository Name"
                      placeholder="owner/repo"
                      value={repoName}
                      onChange={(e) => setRepoName(e.target.value)}
                      margin="normal"
                      variant="outlined"
                    />
                  </Grid>
                  <Grid item xs={4}>
                    <TextField
                      fullWidth
                      label="PR Number"
                      placeholder="123"
                      value={prNumber}
                      onChange={(e) => setPrNumber(e.target.value)}
                      margin="normal"
                      variant="outlined"
                      type="number"
                    />
                  </Grid>
                </Grid>
              </CardContent>
              <CardActions>
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<SearchIcon />}
                  onClick={handleGetPRDetails}
                  disabled={loading}
                >
                  {loading ? 'Loading...' : 'Get Details'}
                </Button>
              </CardActions>
            </Card>
            
            {prDetails && (
              <Card sx={{ mt: 2, maxHeight: 400, overflow: 'auto' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    PR #{prDetails.pr_number} Details
                  </Typography>
                  <Typography variant="body1">
                    <strong>Title:</strong> {prDetails.title}
                  </Typography>
                  <Typography variant="body1">
                    <strong>State:</strong> {prDetails.state}
                  </Typography>
                  <Typography variant="body1">
                    <strong>Created by:</strong> {prDetails.user}
                  </Typography>
                  <Typography variant="body1">
                    <strong>Created at:</strong> {new Date(prDetails.created_at).toLocaleString()}
                  </Typography>
                  <Typography variant="body1">
                    <strong>Updated at:</strong> {new Date(prDetails.updated_at).toLocaleString()}
                  </Typography>
                  <Typography variant="body1">
                    <strong>Merged:</strong> {prDetails.merged ? 'Yes' : 'No'}
                  </Typography>
                  <Typography variant="body1">
                    <strong>Mergeable:</strong> {prDetails.mergeable ? 'Yes' : 'No'}
                  </Typography>
                  <Typography variant="body1">
                    <strong>Comments:</strong> {prDetails.comments}
                  </Typography>
                  <Typography variant="body1">
                    <strong>Commits:</strong> {prDetails.commits}
                  </Typography>
                  <Typography variant="body1">
                    <strong>Changed Files:</strong> {prDetails.changed_files}
                  </Typography>
                  <Typography variant="body1">
                    <strong>Additions:</strong> {prDetails.additions}
                  </Typography>
                  <Typography variant="body1">
                    <strong>Deletions:</strong> {prDetails.deletions}
                  </Typography>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    Description
                  </Typography>
                  <Paper
                    sx={{
                      p: 2,
                      backgroundColor: '#f5f5f5',
                      whiteSpace: 'pre-wrap'
                    }}
                  >
                    {prDetails.body || 'No description provided'}
                  </Paper>
                  <Button
                    variant="outlined"
                    color="primary"
                    href={prDetails.pr_url}
                    target="_blank"
                    sx={{ mt: 2 }}
                  >
                    View on GitHub
                  </Button>
                </CardContent>
              </Card>
            )}
          </Grid>
        </Grid>
      </TabPanel>
      
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

export default CodeExplorer;