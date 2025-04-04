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
  List,
  ListItem,
  ListItemText,
  Chip,
  CircularProgress,
  Alert,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Paper,
  LinearProgress
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import SendIcon from '@mui/icons-material/Send';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import PendingIcon from '@mui/icons-material/Pending';
import RefreshIcon from '@mui/icons-material/Refresh';

function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    documents: 0,
    requirements: 0,
    repositories: 0,
    prReviews: 0,
    workflows: 0
  });
  const [orchestratorStatus, setOrchestratorStatus] = useState({
    running: false,
    loading: false
  });
  const [recentRequirements, setRecentRequirements] = useState([]);
  const [recentPRs, setRecentPRs] = useState([]);
  const [activeWorkflows, setActiveWorkflows] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Simulate API call
        setTimeout(() => {
          setStats({
            documents: 5,
            requirements: 12,
            repositories: 2,
            prReviews: 8,
            workflows: 3
          });
          
          setRecentRequirements([
            { id: 'req-1', title: 'Implement user authentication', status: 'completed', updatedAt: '2025-04-03T14:30:00Z' },
            { id: 'req-2', title: 'Add dashboard analytics', status: 'in_progress', updatedAt: '2025-04-03T16:45:00Z' },
            { id: 'req-3', title: 'Create API documentation', status: 'not_started', updatedAt: '2025-04-02T09:15:00Z' }
          ]);
          
          setRecentPRs([
            { repository: 'org/repo', prNumber: 123, title: 'Add user authentication', status: 'open', reviewResult: 'approved', updatedAt: '2025-04-03T15:20:00Z' },
            { repository: 'org/repo', prNumber: 124, title: 'Fix dashboard bugs', status: 'open', reviewResult: 'changes_requested', updatedAt: '2025-04-03T17:30:00Z' }
          ]);
          
          setActiveWorkflows([
            {
              id: 'wf-1',
              title: 'PR Review Workflow',
              status: 'in_progress',
              progress: 60,
              currentStep: 2,
              steps: [
                { id: 'step-1', title: 'Fetch PR details', status: 'completed' },
                { id: 'step-2', title: 'Analyze code changes', status: 'completed' },
                { id: 'step-3', title: 'Compare with requirements', status: 'in_progress' },
                { id: 'step-4', title: 'Generate review comments', status: 'pending' },
                { id: 'step-5', title: 'Post review to GitHub', status: 'pending' }
              ]
            },
            {
              id: 'wf-2',
              title: 'Requirements Analysis',
              status: 'in_progress',
              progress: 30,
              currentStep: 1,
              steps: [
                { id: 'step-1', title: 'Parse requirement documents', status: 'completed' },
                { id: 'step-2', title: 'Extract requirements', status: 'in_progress' },
                { id: 'step-3', title: 'Validate requirements', status: 'pending' },
                { id: 'step-4', title: 'Store requirements', status: 'pending' }
              ]
            }
          ]);
          
          setOrchestratorStatus({
            running: true,
            loading: false
          });
          
          setLoading(false);
        }, 1000);
        
      } catch (err) {
        setError('Failed to load dashboard data');
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

  const handleStartOrchestrator = async () => {
    try {
      setOrchestratorStatus({ ...orchestratorStatus, loading: true });
      
      setTimeout(() => {
        setOrchestratorStatus({
          running: true,
          loading: false
        });
      }, 1000);
      
    } catch (err) {
      setError('Failed to start orchestrator');
      setOrchestratorStatus({ ...orchestratorStatus, loading: false });
    }
  };

  const handleStopOrchestrator = async () => {
    try {
      setOrchestratorStatus({ ...orchestratorStatus, loading: true });
      
      setTimeout(() => {
        setOrchestratorStatus({
          running: false,
          loading: false
        });
      }, 1000);
      
    } catch (err) {
      setError('Failed to stop orchestrator');
      setOrchestratorStatus({ ...orchestratorStatus, loading: false });
    }
  };

  const handleRefreshData = async () => {
    try {
      setLoading(true);
      
      // Simulate API call
      setTimeout(() => {
        // Update some data to show refresh
        const updatedWorkflows = [...activeWorkflows];
        if (updatedWorkflows.length > 0) {
          const workflow = updatedWorkflows[0];
          workflow.progress = Math.min(100, workflow.progress + 10);
          if (workflow.progress >= 100) {
            workflow.status = 'completed';
            workflow.steps = workflow.steps.map(step => ({ ...step, status: 'completed' }));
          } else if (workflow.currentStep < workflow.steps.length - 1) {
            workflow.currentStep += 1;
            workflow.steps[workflow.currentStep - 1].status = 'completed';
            workflow.steps[workflow.currentStep].status = 'in_progress';
          }
          setActiveWorkflows(updatedWorkflows);
        }
        
        setLoading(false);
      }, 1000);
      
    } catch (err) {
      setError('Failed to refresh data');
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const getRequirementStatusChip = (status) => {
    switch (status) {
      case 'completed':
        return <Chip icon={<CheckCircleIcon />} label="Completed" color="success" size="small" />;
      case 'in_progress':
        return <Chip icon={<PendingIcon />} label="In Progress" color="primary" size="small" />;
      case 'not_started':
        return <Chip label="Not Started" color="default" size="small" />;
      case 'failed':
        return <Chip icon={<ErrorIcon />} label="Failed" color="error" size="small" />;
      default:
        return <Chip label={status} size="small" />;
    }
  };

  const getPRStatusChip = (reviewResult) => {
    switch (reviewResult) {
      case 'approved':
        return <Chip icon={<CheckCircleIcon />} label="Approved" color="success" size="small" />;
      case 'changes_requested':
        return <Chip icon={<ErrorIcon />} label="Changes Requested" color="warning" size="small" />;
      default:
        return <Chip label={reviewResult} size="small" />;
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

  if (loading && !stats.workflows) {
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
          Dashboard
        </Typography>
        <Button 
          variant="outlined" 
          startIcon={<RefreshIcon />} 
          onClick={handleRefreshData}
          disabled={loading}
        >
          Refresh
          {loading && <CircularProgress size={20} sx={{ ml: 1 }} />}
        </Button>
      </Box>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Typography variant="h5" component="div">
                {stats.documents}
              </Typography>
              <Typography color="text.secondary">
                Documents
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Typography variant="h5" component="div">
                {stats.requirements}
              </Typography>
              <Typography color="text.secondary">
                Requirements
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Typography variant="h5" component="div">
                {stats.repositories}
              </Typography>
              <Typography color="text.secondary">
                Repositories
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Typography variant="h5" component="div">
                {stats.prReviews}
              </Typography>
              <Typography color="text.secondary">
                PR Reviews
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Typography variant="h5" component="div">
                {stats.workflows}
              </Typography>
              <Typography color="text.secondary">
                Workflows
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12}>
          <Card>
            <CardHeader title="Task Orchestrator" />
            <Divider />
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Typography variant="body1" sx={{ mr: 2 }}>
                  Status: 
                </Typography>
                {orchestratorStatus.running ? (
                  <Chip label="Running" color="success" />
                ) : (
                  <Chip label="Stopped" color="error" />
                )}
              </Box>
              
              <Box sx={{ display: 'flex', gap: 2 }}>
                {orchestratorStatus.running ? (
                  <Button
                    variant="contained"
                    color="error"
                    startIcon={<StopIcon />}
                    onClick={handleStopOrchestrator}
                    disabled={orchestratorStatus.loading}
                  >
                    Stop
                  </Button>
                ) : (
                  <Button
                    variant="contained"
                    color="primary"
                    startIcon={<PlayArrowIcon />}
                    onClick={handleStartOrchestrator}
                    disabled={orchestratorStatus.loading}
                  >
                    Start
                  </Button>
                )}
                
                {orchestratorStatus.loading && (
                  <CircularProgress size={24} sx={{ ml: 2 }} />
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12}>
          <Card>
            <CardHeader title="Active Workflows" />
            <Divider />
            <CardContent>
              {activeWorkflows.length > 0 ? (
                <Grid container spacing={3}>
                  {activeWorkflows.map((workflow) => (
                    <Grid item xs={12} md={6} key={workflow.id}>
                      <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
                        <Typography variant="h6" gutterBottom>
                          {workflow.title}
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                          <Typography variant="body2" sx={{ mr: 1 }}>
                            Progress:
                          </Typography>
                          <Box sx={{ width: '100%', mr: 1 }}>
                            <LinearProgress 
                              variant="determinate" 
                              value={workflow.progress} 
                              color={workflow.status === 'completed' ? 'success' : 'primary'}
                            />
                          </Box>
                          <Typography variant="body2">
                            {workflow.progress}%
                          </Typography>
                        </Box>
                        <Stepper orientation="vertical" activeStep={workflow.currentStep}>
                          {workflow.steps.map((step, index) => (
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
                              </StepContent>
                            </Step>
                          ))}
                        </Stepper>
                      </Paper>
                    </Grid>
                  ))}
                </Grid>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No active workflows
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Recent Requirements" />
            <Divider />
            <CardContent>
              <List>
                {recentRequirements.length > 0 ? (
                  recentRequirements.map((req) => (
                    <ListItem key={req.id} divider>
                      <ListItemText
                        primary={req.title}
                        secondary={`Updated: ${formatDate(req.updatedAt)}`}
                      />
                      {getRequirementStatusChip(req.status)}
                    </ListItem>
                  ))
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No requirements found
                  </Typography>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Recent PR Reviews" />
            <Divider />
            <CardContent>
              <List>
                {recentPRs.length > 0 ? (
                  recentPRs.map((pr) => (
                    <ListItem key={`${pr.repository}-${pr.prNumber}`} divider>
                      <ListItemText
                        primary={`#${pr.prNumber}: ${pr.title}`}
                        secondary={`${pr.repository} • Updated: ${formatDate(pr.updatedAt)}`}
                      />
                      {getPRStatusChip(pr.reviewResult)}
                    </ListItem>
                  ))
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No PR reviews found
                  </Typography>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Dashboard;