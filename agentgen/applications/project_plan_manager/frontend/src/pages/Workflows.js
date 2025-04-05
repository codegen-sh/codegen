import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Button,
  Divider,
  Chip,
  CircularProgress,
  Alert,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Paper,
  LinearProgress,
  TextField,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayArrowIcon,
  Stop as StopIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Cancel as CancelIcon,
  Info as InfoIcon
} from '@mui/icons-material';

function Workflows() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [workflows, setWorkflows] = useState([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [newWorkflow, setNewWorkflow] = useState({
    title: '',
    description: '',
    type: 'pr_review',
    steps: []
  });

  useEffect(() => {
    fetchWorkflows();
  }, []);

  const fetchWorkflows = async () => {
    try {
      setLoading(true);
      
      // Simulate API call
      setTimeout(() => {
        setWorkflows([
          {
            id: 'wf-1',
            title: 'PR Review Workflow',
            description: 'Automated review of PR #123',
            type: 'pr_review',
            status: 'in_progress',
            progress: 60,
            currentStep: 2,
            steps: [
              { id: 'step-1', title: 'Fetch PR details', status: 'completed', result: { pr_number: 123, repo: 'org/repo' } },
              { id: 'step-2', title: 'Analyze code changes', status: 'completed', result: { files_changed: 5, lines_added: 120, lines_removed: 30 } },
              { id: 'step-3', title: 'Compare with requirements', status: 'in_progress' },
              { id: 'step-4', title: 'Generate review comments', status: 'pending' },
              { id: 'step-5', title: 'Post review to GitHub', status: 'pending' }
            ],
            created_at: '2025-04-03T14:30:00Z',
            updated_at: '2025-04-03T15:45:00Z'
          },
          {
            id: 'wf-2',
            title: 'Requirements Analysis',
            description: 'Extract requirements from documentation',
            type: 'requirements',
            status: 'in_progress',
            progress: 30,
            currentStep: 1,
            steps: [
              { id: 'step-1', title: 'Parse requirement documents', status: 'completed', result: { documents_parsed: 3 } },
              { id: 'step-2', title: 'Extract requirements', status: 'in_progress' },
              { id: 'step-3', title: 'Validate requirements', status: 'pending' },
              { id: 'step-4', title: 'Store requirements', status: 'pending' }
            ],
            created_at: '2025-04-03T10:15:00Z',
            updated_at: '2025-04-03T11:30:00Z'
          },
          {
            id: 'wf-3',
            title: 'Project Plan Generation',
            description: 'Generate project plan from requirements',
            type: 'project_plan',
            status: 'completed',
            progress: 100,
            currentStep: 3,
            steps: [
              { id: 'step-1', title: 'Fetch requirements', status: 'completed', result: { requirements_count: 8 } },
              { id: 'step-2', title: 'Generate tasks', status: 'completed', result: { tasks_generated: 15 } },
              { id: 'step-3', title: 'Create project plan', status: 'completed', result: { plan_id: 'plan-123' } },
              { id: 'step-4', title: 'Notify stakeholders', status: 'completed', result: { notifications_sent: 3 } }
            ],
            created_at: '2025-04-02T09:00:00Z',
            updated_at: '2025-04-02T10:30:00Z'
          }
        ]);
        
        setLoading(false);
      }, 1000);
      
    } catch (err) {
      setError('Failed to load workflows');
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    fetchWorkflows();
  };

  const handleOpenDialog = () => {
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setNewWorkflow({
      title: '',
      description: '',
      type: 'pr_review',
      steps: []
    });
  };

  const handleCreateWorkflow = () => {
    // Simulate API call
    setLoading(true);
    
    setTimeout(() => {
      const newId = `wf-${workflows.length + 1}`;
      const createdAt = new Date().toISOString();
      
      let steps = [];
      if (newWorkflow.type === 'pr_review') {
        steps = [
          { id: `${newId}-step-1`, title: 'Fetch PR details', status: 'pending' },
          { id: `${newId}-step-2`, title: 'Analyze code changes', status: 'pending' },
          { id: `${newId}-step-3`, title: 'Compare with requirements', status: 'pending' },
          { id: `${newId}-step-4`, title: 'Generate review comments', status: 'pending' },
          { id: `${newId}-step-5`, title: 'Post review to GitHub', status: 'pending' }
        ];
      } else if (newWorkflow.type === 'requirements') {
        steps = [
          { id: `${newId}-step-1`, title: 'Parse requirement documents', status: 'pending' },
          { id: `${newId}-step-2`, title: 'Extract requirements', status: 'pending' },
          { id: `${newId}-step-3`, title: 'Validate requirements', status: 'pending' },
          { id: `${newId}-step-4`, title: 'Store requirements', status: 'pending' }
        ];
      } else if (newWorkflow.type === 'project_plan') {
        steps = [
          { id: `${newId}-step-1`, title: 'Fetch requirements', status: 'pending' },
          { id: `${newId}-step-2`, title: 'Generate tasks', status: 'pending' },
          { id: `${newId}-step-3`, title: 'Create project plan', status: 'pending' },
          { id: `${newId}-step-4`, title: 'Notify stakeholders', status: 'pending' }
        ];
      }
      
      const createdWorkflow = {
        id: newId,
        title: newWorkflow.title,
        description: newWorkflow.description,
        type: newWorkflow.type,
        status: 'pending',
        progress: 0,
        currentStep: 0,
        steps,
        created_at: createdAt,
        updated_at: createdAt
      };
      
      setWorkflows([...workflows, createdWorkflow]);
      setLoading(false);
      handleCloseDialog();
    }, 1000);
  };

  const handleStartWorkflow = (workflowId) => {
    setLoading(true);
    
    setTimeout(() => {
      const updatedWorkflows = workflows.map(workflow => {
        if (workflow.id === workflowId) {
          return {
            ...workflow,
            status: 'in_progress',
            progress: 10,
            currentStep: 0,
            steps: workflow.steps.map((step, index) => ({
              ...step,
              status: index === 0 ? 'in_progress' : 'pending'
            })),
            updated_at: new Date().toISOString()
          };
        }
        return workflow;
      });
      
      setWorkflows(updatedWorkflows);
      setLoading(false);
    }, 1000);
  };

  const handleStopWorkflow = (workflowId) => {
    setLoading(true);
    
    setTimeout(() => {
      const updatedWorkflows = workflows.map(workflow => {
        if (workflow.id === workflowId) {
          return {
            ...workflow,
            status: 'cancelled',
            updated_at: new Date().toISOString()
          };
        }
        return workflow;
      });
      
      setWorkflows(updatedWorkflows);
      setLoading(false);
    }, 1000);
  };

  const handleDeleteWorkflow = (workflowId) => {
    setLoading(true);
    
    setTimeout(() => {
      const updatedWorkflows = workflows.filter(workflow => workflow.id !== workflowId);
      setWorkflows(updatedWorkflows);
      setLoading(false);
    }, 1000);
  };

  const handleSelectWorkflow = (workflow) => {
    setSelectedWorkflow(workflow);
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const getStatusChip = (status) => {
    switch (status) {
      case 'pending':
        return <Chip label="Pending" color="default" size="small" />;
      case 'in_progress':
        return <Chip label="In Progress" color="primary" size="small" />;
      case 'completed':
        return <Chip icon={<CheckCircleIcon />} label="Completed" color="success" size="small" />;
      case 'failed':
        return <Chip icon={<ErrorIcon />} label="Failed" color="error" size="small" />;
      case 'cancelled':
        return <Chip icon={<CancelIcon />} label="Cancelled" color="warning" size="small" />;
      default:
        return <Chip label={status} size="small" />;
    }
  };

  const getTypeLabel = (type) => {
    switch (type) {
      case 'pr_review':
        return 'PR Review';
      case 'requirements':
        return 'Requirements';
      case 'project_plan':
        return 'Project Plan';
      case 'custom':
        return 'Custom';
      default:
        return type;
    }
  };

  const getStepStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'in_progress':
        return <CircularProgress size={20} />;
      case 'failed':
        return <ErrorIcon color="error" />;
      default:
        return null;
    }
  };

  if (loading && workflows.length === 0) {
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
          Workflows
        </Typography>
        <Box>
          <Button 
            variant="outlined" 
            startIcon={<RefreshIcon />} 
            onClick={handleRefresh}
            disabled={loading}
            sx={{ mr: 2 }}
          >
            Refresh
          </Button>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />} 
            onClick={handleOpenDialog}
            disabled={loading}
          >
            New Workflow
          </Button>
        </Box>
      </Box>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 3 }}>
            <CardHeader title="Workflow List" />
            <Divider />
            <CardContent sx={{ p: 0 }}>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Title</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {workflows.map((workflow) => (
                      <TableRow 
                        key={workflow.id} 
                        hover 
                        selected={selectedWorkflow?.id === workflow.id}
                        onClick={() => handleSelectWorkflow(workflow)}
                        sx={{ cursor: 'pointer' }}
                      >
                        <TableCell>{workflow.title}</TableCell>
                        <TableCell>{getTypeLabel(workflow.type)}</TableCell>
                        <TableCell>{getStatusChip(workflow.status)}</TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex' }}>
                            {workflow.status === 'pending' && (
                              <Tooltip title="Start Workflow">
                                <IconButton 
                                  size="small" 
                                  color="primary"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleStartWorkflow(workflow.id);
                                  }}
                                >
                                  <PlayArrowIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            )}
                            {workflow.status === 'in_progress' && (
                              <Tooltip title="Stop Workflow">
                                <IconButton 
                                  size="small" 
                                  color="error"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleStopWorkflow(workflow.id);
                                  }}
                                >
                                  <StopIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            )}
                            <Tooltip title="Delete Workflow">
                              <IconButton 
                                size="small" 
                                color="error"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDeleteWorkflow(workflow.id);
                                }}
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={8}>
          {selectedWorkflow ? (
            <Card>
              <CardHeader 
                title={selectedWorkflow.title} 
                subheader={selectedWorkflow.description}
                action={
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    {getStatusChip(selectedWorkflow.status)}
                  </Box>
                }
              />
              <Divider />
              <CardContent>
                <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
                  <Tabs value={tabValue} onChange={handleTabChange}>
                    <Tab label="Progress" />
                    <Tab label="Details" />
                  </Tabs>
                </Box>
                
                {tabValue === 0 && (
                  <Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                      <Typography variant="body2" sx={{ mr: 1 }}>
                        Progress:
                      </Typography>
                      <Box sx={{ width: '100%', mr: 1 }}>
                        <LinearProgress 
                          variant="determinate" 
                          value={selectedWorkflow.progress} 
                          color={selectedWorkflow.status === 'completed' ? 'success' : 'primary'}
                        />
                      </Box>
                      <Typography variant="body2">
                        {selectedWorkflow.progress}%
                      </Typography>
                    </Box>
                    
                    <Stepper orientation="vertical" activeStep={selectedWorkflow.currentStep}>
                      {selectedWorkflow.steps.map((step, index) => (
                        <Step key={step.id}>
                          <StepLabel 
                            optional={
                              <Typography variant="caption">
                                {step.status}
                              </Typography>
                            }
                            icon={getStepStatusIcon(step.status)}
                          >
                            {step.title}
                          </StepLabel>
                          <StepContent>
                            <Typography variant="body2" color="text.secondary">
                              {step.status === 'in_progress' ? 'Currently processing...' : ''}
                            </Typography>
                            {step.result && (
                              <Box sx={{ mt: 1, p: 1, bgcolor: 'background.paper', borderRadius: 1 }}>
                                <Typography variant="caption" color="text.secondary">
                                  Result:
                                </Typography>
                                <pre style={{ margin: 0, fontSize: '0.75rem', overflow: 'auto' }}>
                                  {JSON.stringify(step.result, null, 2)}
                                </pre>
                              </Box>
                            )}
                          </StepContent>
                        </Step>
                      ))}
                    </Stepper>
                  </Box>
                )}
                
                {tabValue === 1 && (
                  <Box>
                    <Grid container spacing={2}>
                      <Grid item xs={12} sm={6}>
                        <Typography variant="subtitle2">Type:</Typography>
                        <Typography variant="body2">{getTypeLabel(selectedWorkflow.type)}</Typography>
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <Typography variant="subtitle2">Status:</Typography>
                        <Typography variant="body2">{selectedWorkflow.status}</Typography>
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <Typography variant="subtitle2">Created:</Typography>
                        <Typography variant="body2">{formatDate(selectedWorkflow.created_at)}</Typography>
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <Typography variant="subtitle2">Last Updated:</Typography>
                        <Typography variant="body2">{formatDate(selectedWorkflow.updated_at)}</Typography>
                      </Grid>
                      <Grid item xs={12}>
                        <Typography variant="subtitle2">Description:</Typography>
                        <Typography variant="body2">{selectedWorkflow.description || 'No description provided'}</Typography>
                      </Grid>
                      <Grid item xs={12}>
                        <Typography variant="subtitle2">Steps:</Typography>
                        <Typography variant="body2">{selectedWorkflow.steps.length} steps defined</Typography>
                      </Grid>
                    </Grid>
                  </Box>
                )}
              </CardContent>
            </Card>
          ) : (
            <Paper sx={{ p: 3, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
              <InfoIcon color="disabled" sx={{ fontSize: 60, mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                Select a workflow to view details
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Or create a new workflow using the button above
              </Typography>
            </Paper>
          )}
        </Grid>
      </Grid>
      
      {/* Create Workflow Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Workflow</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Title"
            fullWidth
            variant="outlined"
            value={newWorkflow.title}
            onChange={(e) => setNewWorkflow({ ...newWorkflow, title: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            variant="outlined"
            multiline
            rows={3}
            value={newWorkflow.description}
            onChange={(e) => setNewWorkflow({ ...newWorkflow, description: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            select
            margin="dense"
            label="Workflow Type"
            fullWidth
            variant="outlined"
            value={newWorkflow.type}
            onChange={(e) => setNewWorkflow({ ...newWorkflow, type: e.target.value })}
          >
            <MenuItem value="pr_review">PR Review</MenuItem>
            <MenuItem value="requirements">Requirements</MenuItem>
            <MenuItem value="project_plan">Project Plan</MenuItem>
            <MenuItem value="custom">Custom</MenuItem>
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button 
            onClick={handleCreateWorkflow} 
            variant="contained" 
            disabled={!newWorkflow.title}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Workflows;