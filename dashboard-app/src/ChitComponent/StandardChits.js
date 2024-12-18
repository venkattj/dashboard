import React, { useEffect, useState } from 'react';
import {
  Grid,
  Paper,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Snackbar,
} from '@mui/material';
import styled from 'styled-components';
import api from '../api'; // Import your API module for making requests
import MuiAlert from '@mui/material/Alert';
import moment from 'moment'; // Import moment.js for date calculations
import { useNavigate } from 'react-router-dom'; // Update this import

const ChitContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(45deg, #4a90e2, #50a7c2);
  padding: 20px;
  color: white;
`;

const Header = styled.h1`
  text-align: center;
  margin-bottom: 40px;
  font-size: 2.5rem;
`;

const Widget = styled(Paper)`
  padding: 20px;
  text-align: center;
  background-color: rgba(255, 255, 255, 0.1) !important;
  color: white !important;
  cursor: pointer; /* Makes the widget appear clickable */
`;

const ChitForm = styled.div`
  display: flex;
  flex-direction: column;
`;

const ChitItem = styled.div`
  margin: 10px 0;
`;

const Alert = React.forwardRef(function Alert(props, ref) {
  return <MuiAlert elevation={6} ref={ref} variant="filled" {...props} />;
});

const StandardChits = () => {
  const [chits, setChits] = useState([]);
  const [open, setOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [currentChit, setCurrentChit] = useState(null);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });

  const [formData, setFormData] = useState({
    organisation: '',
    value: '',
    duration: '',
    emi: '',
    maturity: '',
    started: '',
    emiPaid: '',      // New field
    nextEmiDate: '',  // New field
    currentValue: '',  // New field
  });

  const navigate = useNavigate(); // Use useNavigate instead of useHistory

  useEffect(() => {
    fetchChits();
  }, []);

  const fetchChits = async () => {
    try {
      const response = await api.get('/api/chits');
      const updatedChits = response.data.map(chit => {
        const currentDate = moment();
        const startedDate = moment(chit.started);
        const durationMonths = parseInt(chit.duration, 10);

        // Calculate the number of EMIs paid
        const monthsDiff = currentDate.diff(startedDate, 'months');
        const emIsPaid = Math.min(monthsDiff, durationMonths) + 1; // Ensure it doesn't exceed duration

        // Calculate the next EMI date
        const nextEmiDate = startedDate.add(emIsPaid + 1, 'months').format('YYYY-MM-DD');

        // Calculate current value
        const currentValue = chit.value * emIsPaid / chit.duration;

        return {
          ...chit,
          emiPaid: emIsPaid,
          nextEmiDate,
          currentValue: currentValue > 0 ? currentValue : 0, // Ensure current value doesn't go below zero
        };
      });

      setChits(updatedChits);
    } catch (error) {
      console.error('Error fetching chits:', error);
    }
  };

  const handleOpen = () => {
    setOpen(true);
    setFormData({
      organisation: '',
      value: '',
      duration: '',
      emi: '',
      maturity: '',
      started: '',
      emiPaid: '',       // Reset new field
      nextEmiDate: '',   // Reset new field
      currentValue: '',   // Reset new field
    });
    setIsEditing(false);
  };

  const handleEdit = (chit) => {
    setOpen(true);
    setIsEditing(true);
    setCurrentChit(chit);
    setFormData({
      organisation: chit.organisation,
      value: chit.value,
      duration: chit.duration,
      emi: chit.emi || '',
      maturity: chit.maturity,
      started: chit.started,
      emiPaid: chit.emiPaid || '',       // Set new field
      nextEmiDate: chit.nextEmiDate || '',  // Set new field
      currentValue: chit.currentValue || '', // Set new field
    });
  };

  const handleClose = () => {
    setOpen(false);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (isEditing) {
        await api.put(`/api/chits/${currentChit.sno}`, formData);
        setNotification({ open: true, message: 'Chit updated successfully!', severity: 'success' });
      } else {
        await api.post('/api/chits', formData);
        setNotification({ open: true, message: 'Chit created successfully!', severity: 'success' });
      }
      fetchChits();
      handleClose();
    } catch (error) {
      setNotification({ open: true, message: 'Error saving chit!', severity: 'error' });
    }
  };

  const handleDelete = async (sno) => {
    try {
      await api.delete(`/api/chits/${sno}`);
      setNotification({ open: true, message: 'Chit deleted successfully!', severity: 'success' });
      fetchChits();
    } catch (error) {
      setNotification({ open: true, message: 'Error deleting chit!', severity: 'error' });
    }
  };

  const handleNotificationClose = () => {
    setNotification({ ...notification, open: false });
  };

  // Calculate total current value
  const totalCurrentValue = chits.reduce((total, chit) => total + chit.currentValue, 0);

  const handleBack = () => {
    navigate(-1); // Navigate back to the previous page
  };

  return (
    <ChitContainer>
      <Button variant="contained" color="primary" onClick={handleBack} >
         Back to Chits Dashboard
      </Button>
      <Header>Standard Chits</Header>
      <Button variant="contained" color="secondary" onClick={handleOpen} style={{ marginLeft: '20px' }}>
        Add New Chit
      </Button>
      <Grid container spacing={3} style={{ marginTop: '20px' }}>
        {chits.map((chit) => (
          <Grid item xs={12} sm={6} md={4} key={chit.sno}>
            <Widget>
              <h2>{chit.organisation}</h2>
              <p>Value: ₹{chit.value}</p>
              <p>Duration: {chit.duration} months</p>
              <p>EMI: ₹{chit.emi || 'N/A'}</p>
              <p>EMIs Paid: {chit.emiPaid || 'N/A'}</p>      {/* New field */}
              <p>Next EMI Date: {chit.nextEmiDate || 'N/A'}</p>  {/* New field */}
              <p>Current Value: ₹{chit.currentValue || 'N/A'}</p>  {/* New field */}
              <p>Maturity Date: {chit.maturity}</p>
              <p>Started On: {chit.started}</p>
              <Button variant="outlined" color="secondary" onClick={() => handleEdit(chit)}>
                Edit
              </Button>
              <Button variant="outlined" color="error" onClick={() => handleDelete(chit.sno)}>
                Delete
              </Button>
            </Widget>
          </Grid>
        ))}
      </Grid>

      {/* Total Current Value Display */}
      <div style={{ textAlign: 'center', marginTop: '20px', color: 'white' }}>
        <h2>Total Value: ₹{totalCurrentValue}</h2>
      </div>

      <Dialog open={open} onClose={handleClose}>
        <DialogTitle>{isEditing ? 'Edit Chit' : 'Add New Chit'}</DialogTitle>
        <DialogContent>
          <ChitForm>
            <ChitItem>
              <TextField
                label="Organisation"
                name="organisation"
                value={formData.organisation}
                onChange={handleChange}
                fullWidth
                required
              />
            </ChitItem>
            <ChitItem>
              <TextField
                label="Value"
                name="value"
                type="number"
                value={formData.value}
                onChange={handleChange}
                fullWidth
                required
              />
            </ChitItem>
            <ChitItem>
              <TextField
                label="Duration (months)"
                name="duration"
                type="number"
                value={formData.duration}
                onChange={handleChange}
                fullWidth
                required
              />
            </ChitItem>
            <ChitItem>
              <TextField
                label="EMI"
                name="emi"
                type="number"
                value={formData.emi}
                onChange={handleChange}
                fullWidth
              />
            </ChitItem>
            <ChitItem>
              <TextField
                label="Maturity Date"
                name="maturity"
                type="date"
                value={formData.maturity}
                onChange={handleChange}
                fullWidth
                InputLabelProps={{ shrink: true }}
                required
              />
            </ChitItem>
            <ChitItem>
              <TextField
                label="Started On"
                name="started"
                type="date"
                value={formData.started}
                onChange={handleChange}
                fullWidth
                InputLabelProps={{ shrink: true }}
                required
              />
            </ChitItem>
          </ChitForm>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} color="primary">
            Cancel
          </Button>
          <Button onClick={handleSubmit} color="primary">
            {isEditing ? 'Update' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={notification.open} autoHideDuration={6000} onClose={handleNotificationClose}>
        <Alert onClose={handleNotificationClose} severity={notification.severity}>
          {notification.message}
        </Alert>
      </Snackbar>
    </ChitContainer>
  );
};

export default StandardChits;
