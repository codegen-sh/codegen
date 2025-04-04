import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardActions,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Grid,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Assignment as ExtractIcon,
} from '@mui/icons-material';
import axios from 'axios';

function Documents() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [currentDocument, setCurrentDocument] = useState(null);
  const [documentName, setDocumentName] = useState('');
  const [documentContent, setDocumentContent] = useState('');
  const [file, setFile] = useState(null);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/documents');
      setDocuments(response.data);
    } catch (error) {
      console.error('Error fetching documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadDialogOpen = () => {
    setUploadDialogOpen(true);
  };

  const handleUploadDialogClose = () => {
    setUploadDialogOpen(false);
    setDocumentName('');
    setDocumentContent('');
    setFile(null);
  };

  const handleViewDocument = (document) => {
    setCurrentDocument(document);
    setViewDialogOpen(true);
  };

  const handleViewDialogClose = () => {
    setViewDialogOpen(false);
    setCurrentDocument(null);
  };

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleUploadDocument = async () => {
    try {
      if (file) {
        const formData = new FormData();
        formData.append('name', documentName);
        formData.append('file', file);
        
        await axios.post('/documents/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
      } else {
        await axios.post('/documents', {
          id: '',
          name: documentName,
          content: documentContent,
          requirements: [],
        });
      }
      
      handleUploadDialogClose();
      fetchDocuments();
    } catch (error) {
      console.error('Error uploading document:', error);
    }
  };

  const handleDeleteDocument = async (documentId) => {
    try {
      await axios.delete(`/documents/${documentId}`);
      fetchDocuments();
    } catch (error) {
      console.error('Error deleting document:', error);
    }
  };

  const handleExtractRequirements = async (documentId) => {
    try {
      await axios.post(`/requirements/extract`, { document_id: documentId });
      // Show success message or redirect to requirements page
    } catch (error) {
      console.error('Error extracting requirements:', error);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Documents</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleUploadDialogOpen}
        >
          Upload Document
        </Button>
      </Box>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      ) : documents.length === 0 ? (
        <Card>
          <CardContent>
            <Typography variant="h6" align="center">
              No documents found
            </Typography>
            <Typography variant="body2" align="center" color="text.secondary">
              Upload a document to get started
            </Typography>
          </CardContent>
          <CardActions sx={{ justifyContent: 'center' }}>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleUploadDialogOpen}
            >
              Upload Document
            </Button>
          </CardActions>
        </Card>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Created At</TableCell>
                <TableCell>Updated At</TableCell>
                <TableCell>Requirements</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {documents.map((document) => (
                <TableRow key={document.id}>
                  <TableCell>{document.name}</TableCell>
                  <TableCell>{new Date(document.created_at).toLocaleString()}</TableCell>
                  <TableCell>{new Date(document.updated_at).toLocaleString()}</TableCell>
                  <TableCell>{document.requirements.length}</TableCell>
                  <TableCell>
                    <IconButton
                      color="primary"
                      onClick={() => handleViewDocument(document)}
                      title="View Document"
                    >
                      <ViewIcon />
                    </IconButton>
                    <IconButton
                      color="secondary"
                      onClick={() => handleExtractRequirements(document.id)}
                      title="Extract Requirements"
                    >
                      <ExtractIcon />
                    </IconButton>
                    <IconButton
                      color="error"
                      onClick={() => handleDeleteDocument(document.id)}
                      title="Delete Document"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Upload Document Dialog */}
      <Dialog open={uploadDialogOpen} onClose={handleUploadDialogClose} maxWidth="md" fullWidth>
        <DialogTitle>Upload Document</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Upload a document containing requirements. You can either upload a file or enter the content directly.
          </DialogContentText>
          <TextField
            autoFocus
            margin="dense"
            id="name"
            label="Document Name"
            type="text"
            fullWidth
            variant="outlined"
            value={documentName}
            onChange={(e) => setDocumentName(e.target.value)}
            sx={{ mb: 2 }}
          />
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Typography variant="subtitle1">Upload File</Typography>
              <input
                type="file"
                accept=".md,.txt,.doc,.docx"
                onChange={handleFileChange}
              />
            </Grid>
            <Grid item xs={12}>
              <Typography variant="subtitle1">Or Enter Content Directly</Typography>
              <TextField
                margin="dense"
                id="content"
                label="Document Content"
                multiline
                rows={10}
                fullWidth
                variant="outlined"
                value={documentContent}
                onChange={(e) => setDocumentContent(e.target.value)}
                disabled={!!file}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleUploadDialogClose}>Cancel</Button>
          <Button
            onClick={handleUploadDocument}
            variant="contained"
            disabled={!documentName || (!file && !documentContent)}
          >
            Upload
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Document Dialog */}
      <Dialog open={viewDialogOpen} onClose={handleViewDialogClose} maxWidth="md" fullWidth>
        <DialogTitle>{currentDocument?.name}</DialogTitle>
        <DialogContent>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Created: {currentDocument && new Date(currentDocument.created_at).toLocaleString()}
          </Typography>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Updated: {currentDocument && new Date(currentDocument.updated_at).toLocaleString()}
          </Typography>
          <Paper variant="outlined" sx={{ p: 2, mt: 2, maxHeight: '60vh', overflow: 'auto' }}>
            <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>
              {currentDocument?.content}
            </pre>
          </Paper>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleViewDialogClose}>Close</Button>
          <Button
            onClick={() => {
              handleExtractRequirements(currentDocument.id);
              handleViewDialogClose();
            }}
            variant="contained"
            startIcon={<ExtractIcon />}
          >
            Extract Requirements
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Documents;