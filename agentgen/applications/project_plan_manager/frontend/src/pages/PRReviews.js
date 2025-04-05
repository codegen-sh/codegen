import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Button, 
  TextField, 
  Grid, 
  Card, 
  CardContent, 
  CardActions,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  Divider,
  CircularProgress,
  Alert,
  Snackbar
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { GitHub, Refresh, Add, Check, Close, Comment, Merge } from '@mui/icons-material';
import axios from 'axios';

function PRReviews() {
  const [prReviews, setPRReviews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [openCreateDialog, setOpenCreateDialog] = useState(false);
  const [openViewDialog, setOpenViewDialog] = useState(false);
  const [selectedPR, setSelectedPR] = useState(null);
  const [newPR, setNewPR] = useState({
    pr_number: '',
    repo: '',
    title: '',
    description: ''
  });
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'info'
  });

  useEffect(() => {
    fetchPRReviews();
  }, []);

  const fetchPRReviews = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get('/api/pr-reviews');
      setPRReviews(response.data);
    } catch (err) {
      setError('Failed to fetch PR reviews: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePR = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post('/api/pr-reviews', {
        pr_number: parseInt(newPR.pr_number),
        repo: newPR.repo,
        title: newPR.title,
        description: newPR.description
      });
      setPRReviews([...prReviews, response.data]);
      setOpenCreateDialog(false);
      setNewPR({
        pr_number: '',
        repo: '',
        title: '',
        description: ''
      });
      setSnackbar({
        open: true,
        message: 'PR review created successfully',
        severity: 'success'
      });
    } catch (err) {
      setError('Failed to create PR review: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handlePostToGitHub = async (prId) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(`/api/pr-reviews/${prId}/post-to-github`);
      fetchPRReviews();
      setSnackbar({
        open: true,
        message: 'Review posted to GitHub successfully',
        severity: 'success'
      });
    } catch (err) {
      setError('Failed to post review to GitHub: ' + (err.response?.data?.detail || err.message));
      setSnackbar({
        open: true,
        message: 'Failed to post review to GitHub: ' + (err.response?.data?.detail || err.message),
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleAutoMergePR = async (prId) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(`/api/pr-reviews/${prId}/auto-merge`);
      fetchPRReviews();
      setSnackbar({
        open: true,
        message: 'PR auto-merged successfully',
        severity: 'success'
      });
    } catch (err) {
      setError('Failed to auto-merge PR: ' + (err.response?.data?.detail || err.message));
      setSnackbar({
        open: true,
        message: 'Failed to auto-merge PR: ' + (err.response?.data?.detail || err.message),
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleViewPR = (pr) => {
    setSelectedPR(pr);
    setOpenViewDialog(true);
  };

  const getStatusChip = (status) => {
    switch (status) {
      case 'pending':
        return <Chip label="Pending" color="default" size="small" />;
      case 'in_progress':
        return <Chip label="In Progress" color="primary" size="small" />;
      case 'completed':
        return <Chip label="Completed" color="success" size="small" />;
      case 'failed':
        return <Chip label="Failed" color="error" size="small" />;
      case 'cancelled':
        return <Chip label="Cancelled" color="warning" size="small" />;
      default:
        return <Chip label={status} size="small" />;
    }
  };

  const columns = [
    { field: 'pr_number', headerName: 'PR #', width: 100 },
    { field: 'repo', headerName: 'Repository', width: 200 },
    { field: 'title', headerName: 'Title', width: 300 },
    { 
      field: 'status', 
      headerName: 'Status', 
      width: 150,
      renderCell: (params) => getStatusChip(params.value)
    },
    { 
      field: 'created_at', 
      headerName: 'Created', 
      width: 200,
      valueFormatter: (params) => new Date(params.value).toLocaleString()
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 300,
      renderCell: (params) => (
        <Box>
          <Button 
            variant="outlined" 
            size="small" 
            onClick={() => handleViewPR(params.row)}
            sx={{ mr: 1 }}
          >
            View
          </Button>
          {params.row.status === 'completed' && (
            <Button 
              variant="outlined" 
              color="primary" 
              size="small" 
              onClick={() => handlePostToGitHub(params.row.id)}
              startIcon={<Comment />}
              sx={{ mr: 1 }}
            >
              Post to GitHub
            </Button>
          )}
          {params.row.status === 'completed' && (
            <Button 
              variant="outlined" 
              color="success" 
              size="small" 
              onClick={() => handleAutoMergePR(params.row.id)}
              startIcon={<Merge />}
            >
              Auto-Merge
            </Button>
          )}
        </Box>
      )
    }
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h4" gutterBottom>
          PR Reviews
        </Typography>
        <Box>
          <Button 
            variant="contained" 
            color="primary" 
            startIcon={<Add />}
            onClick={() => setOpenCreateDialog(true)}
            sx={{ mr: 1 }}
          >
            New PR Review
          </Button>
          <Button 
            variant="outlined" 
            startIcon={<Refresh />}
            onClick={fetchPRReviews}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ height: 400, width: '100%' }}>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
              <CircularProgress />
            </Box>
          ) : (
            <DataGrid
              rows={prReviews}
              columns={columns}
              pageSize={5}
              rowsPerPageOptions={[5, 10, 20]}
              disableSelectionOnClick
              autoHeight
            />
          )}
        </Box>
      </Paper>

      {/* Create PR Dialog */}
      <Dialog open={openCreateDialog} onClose={() => setOpenCreateDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create New PR Review</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={6}>
              <TextField
                label="PR Number"
                type="number"
                fullWidth
                value={newPR.pr_number}
                onChange={(e) => setNewPR({ ...newPR, pr_number: e.target.value })}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                label="Repository"
                fullWidth
                value={newPR.repo}
                onChange={(e) => setNewPR({ ...newPR, repo: e.target.value })}
                placeholder="owner/repo"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Title"
                fullWidth
                value={newPR.title}
                onChange={(e) => setNewPR({ ...newPR, title: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Description"
                fullWidth
                multiline
                rows={4}
                value={newPR.description}
                onChange={(e) => setNewPR({ ...newPR, description: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCreateDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleCreatePR} 
            variant="contained" 
            color="primary"
            disabled={!newPR.pr_number || !newPR.repo || !newPR.title}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* View PR Dialog */}
      <Dialog open={openViewDialog} onClose={() => setOpenViewDialog(false)} maxWidth="md" fullWidth>
        {selectedPR && (
          <>
            <DialogTitle>
              PR #{selectedPR.pr_number}: {selectedPR.title}
            </DialogTitle>
            <DialogContent>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1" gutterBottom>Repository</Typography>
                  <Typography variant="body1" gutterBottom>{selectedPR.repo}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1" gutterBottom>Status</Typography>
                  <Typography variant="body1" gutterBottom>{getStatusChip(selectedPR.status)}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle1" gutterBottom>Description</Typography>
                  <Typography variant="body1" gutterBottom>{selectedPR.description || 'No description'}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle1" gutterBottom>Comments</Typography>
                  {selectedPR.comments && selectedPR.comments.length > 0 ? (
                    <List>
                      {selectedPR.comments.map((comment) => (
                        <React.Fragment key={comment.id}>
                          <ListItem alignItems="flex-start">
                            <ListItemText
                              primary={comment.file ? `${comment.file}:${comment.line}` : 'General Comment'}
                              secondary={comment.body}
                            />
                          </ListItem>
                          <Divider component="li" />
                        </React.Fragment>
                      ))}
                    </List>
                  ) : (
                    <Typography variant="body1">No comments yet</Typography>
                  )}
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle1" gutterBottom>Workflow</Typography>
                  {selectedPR.workflow_id ? (
                    <Typography variant="body1">Workflow ID: {selectedPR.workflow_id}</Typography>
                  ) : (
                    <Typography variant="body1">No workflow associated</Typography>
                  )}
                </Grid>
              </Grid>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setOpenViewDialog(false)}>Close</Button>
              {selectedPR.status === 'completed' && (
                <>
                  <Button 
                    onClick={() => handlePostToGitHub(selectedPR.id)} 
                    color="primary"
                    startIcon={<Comment />}
                  >
                    Post to GitHub
                  </Button>
                  <Button 
                    onClick={() => handleAutoMergePR(selectedPR.id)} 
                    color="success"
                    startIcon={<Merge />}
                  >
                    Auto-Merge
                  </Button>
                </>
              )}
            </DialogActions>
          </>
        )}
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert 
          onClose={() => setSnackbar({ ...snackbar, open: false })} 
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default PRReviews;