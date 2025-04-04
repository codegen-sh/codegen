import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  CardActions,
  Button,
  Typography,
  Grid,
  CircularProgress,
} from '@mui/material';
import axios from 'axios';

function Dashboard() {
  const [stats, setStats] = useState({
    documents: 0,
    requirements: 0,
    repositories: 0,
    prReviews: 0,
    projectPlans: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        
        // Fetch counts from API
        const [documents, requirements, repositories, prReviews, projectPlans] = await Promise.all([
          axios.get('/documents'),
          axios.get('/requirements'),
          axios.get('/repositories'),
          axios.get('/pr-reviews'),
          axios.get('/project-plans'),
        ]);
        
        setStats({
          documents: documents.data.length,
          requirements: requirements.data.length,
          repositories: repositories.data.length,
          prReviews: prReviews.data.length,
          projectPlans: projectPlans.data.length,
        });
      } catch (error) {
        console.error('Error fetching stats:', error);
        // Set default values if API is not available
        setStats({
          documents: 0,
          requirements: 0,
          repositories: 0,
          prReviews: 0,
          projectPlans: 0,
        });
      } finally {
        setLoading(false);
      }
    };
    
    fetchStats();
  }, []);

  const statCards = [
    {
      title: 'Documents',
      count: stats.documents,
      description: 'Requirement documents uploaded to the system',
      link: '/documents',
    },
    {
      title: 'Requirements',
      count: stats.requirements,
      description: 'Individual requirements extracted from documents',
      link: '/requirements',
    },
    {
      title: 'Repositories',
      count: stats.repositories,
      description: 'GitHub repositories configured for tracking',
      link: '/repositories',
    },
    {
      title: 'PR Reviews',
      count: stats.prReviews,
      description: 'Pull request reviews performed by the agent',
      link: '/pr-reviews',
    },
    {
      title: 'Project Plans',
      count: stats.projectPlans,
      description: 'AI-generated project plans for implementation',
      link: '/project-plans',
    },
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      
      <Typography variant="body1" paragraph>
        Welcome to the Integrated Agent dashboard. This application combines PR Review Agent and Requirements Tracker
        to provide a seamless workflow for tracking requirements, reviewing PRs, and coordinating with Codegen.
      </Typography>
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={3} sx={{ mt: 2 }}>
          {statCards.map((card) => (
            <Grid item xs={12} sm={6} md={4} key={card.title}>
              <Card>
                <CardContent>
                  <Typography variant="h5" component="div">
                    {card.title}
                  </Typography>
                  <Typography variant="h3" color="primary" sx={{ my: 2 }}>
                    {card.count}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {card.description}
                  </Typography>
                </CardContent>
                <CardActions>
                  <Button size="small" component={Link} to={card.link}>
                    View {card.title}
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
      
      <Box sx={{ mt: 4 }}>
        <Typography variant="h5" gutterBottom>
          Quick Actions
        </Typography>
        <Grid container spacing={2}>
          <Grid item>
            <Button variant="contained" component={Link} to="/documents">
              Upload Document
            </Button>
          </Grid>
          <Grid item>
            <Button variant="contained" component={Link} to="/repositories">
              Add Repository
            </Button>
          </Grid>
          <Grid item>
            <Button variant="contained" component={Link} to="/project-plans">
              Generate Plan
            </Button>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
}

export default Dashboard;