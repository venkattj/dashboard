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
import moment from 'moment';

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
  cursor: pointer;
`;

const ChitForm = styled.div`
  display: flex;
  flex-direction: column;
`;

const ChitItem = styled.div`
  margin: 10px 0;
`;

const EmiTable = styled.div`
  margin-top: 20px;
`;

const EmiRow = styled.div`
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  padding: 10px;
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
`;

const Alert = React.forwardRef(function Alert(props, ref) {
  return <MuiAlert elevation={6} ref={ref} variant="filled" {...props} />;
});

const VariableChits = () => {
  const [variableChits, setVariableChits] = useState([]);
  const [open, setOpen] = useState(false);
  const [openEmi, setOpenEmi] = useState(false); // For EMI dialog
  const [isEditing, setIsEditing] = useState(false);
  const [isEditingEmi, setIsEditingEmi] = useState(false);
  const [currentChit, setCurrentChit] = useState(null);
  const [currentEmi, setCurrentEmi] = useState(null);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });

  const [formData, setFormData] = useState({
    organisation: '',
    value: '',
    duration: '',
    emi: '',
    maturity: '',
    started: '',
  });

  const [emiFormData, setEmiFormData] = useState({
    emi_no: '',
    amount: '',
    emi_date: '',
  });

  useEffect(() => {
    fetchVariableChits();
  }, []);

  const fetchVariableChits = async () => {
    try {
      const response = await api.get('/api/variable_chits');
      setVariableChits(response.data);
    } catch (error) {
      console.error('Error fetching variable chits:', error);
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
      emi: chit.emi,
      maturity: chit.maturity,
      started: chit.started,
    });
  };

  const handleClose = () => {
    setOpen(false);
  };

  const handleCloseEmi = () => {
    setOpenEmi(false);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleEmiChange = (e) => {
    const { name, value } = e.target;
    setEmiFormData({ ...emiFormData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (isEditing) {
        await api.put(`/api/chits/${currentChit.chit_id}`, formData);
        setNotification({ open: true, message: 'Variable chit updated successfully!', severity: 'success' });
      } else {
        await api.post('/api/chits', formData); // Adjust endpoint if necessary
        setNotification({ open: true, message: 'Variable chit created successfully!', severity: 'success' });
      }
      fetchVariableChits();
      handleClose();
    } catch (error) {
      setNotification({ open: true, message: 'Error saving variable chit!', severity: 'error' });
    }
  };

  const handleDelete = async (chit_id) => {
    try {
      await api.delete(`/api/chits/${chit_id}`);
      setNotification({ open: true, message: 'Variable chit deleted successfully!', severity: 'success' });
      fetchVariableChits();
    } catch (error) {
      setNotification({ open: true, message: 'Error deleting variable chit!', severity: 'error' });
    }
  };

  const handleAddEmi = (chit) => {
    setCurrentChit(chit);
    setOpenEmi(true);
    setEmiFormData({
      emi_no: '',
      amount: '',
      emi_date: '',
    });
    setIsEditingEmi(false);
  };

  const handleEditEmi = (chit, emi) => {
    setCurrentChit(chit);
    setCurrentEmi(emi);
    setOpenEmi(true);
    setEmiFormData({
      emi_no: emi.emi_no,
      amount: emi.amount,
      emi_date: moment(emi.emi_date).format('YYYY-MM-DD'),
    });
    setIsEditingEmi(true);
  };

  const handleSubmitEmi = async (e) => {
    e.preventDefault();
    try {
      if (isEditingEmi) {
        await api.put(`/api/variable_chits/${currentChit.chit_id}/emis/${currentEmi.id}`, emiFormData);
        setNotification({ open: true, message: 'EMI updated successfully!', severity: 'success' });
      } else {
        await api.post(`/api/variable_chits/${currentChit.chit_id}/emis`, emiFormData);
        setNotification({ open: true, message: 'EMI added successfully!', severity: 'success' });
      }
      fetchVariableChits();
      handleCloseEmi();
    } catch (error) {
      setNotification({ open: true, message: 'Error saving EMI!', severity: 'error' });
    }
  };

  const handleDeleteEmi = async (chit_id, emi_id) => {
    try {
      await api.delete(`/api/variable_chits/${chit_id}/emis/${emi_id}`);
      setNotification({ open: true, message: 'EMI deleted successfully!', severity: 'success' });
      fetchVariableChits();
    } catch (error) {
      setNotification({ open: true, message: 'Error deleting EMI!', severity: 'error' });
    }
  };

  const handleNotificationClose = () => {
    setNotification({ ...notification, open: false });
  };

  const calculateTotalEmiPaid = (emis) => {
      return emis.reduce((total, emi) => total + Number(emi.amount ?? 0), 0);
  };


  const getNextEmiDate = (emis) => {
    // Sort the EMIs by date to get the most recent one
    const sortedEmis = emis.sort((a, b) => moment(a.emi_date).diff(moment(b.emi_date)));
    const lastEmi = sortedEmis[sortedEmis.length - 1];

    // If there are EMIs, return the last EMI date + 1 month, else return a default message
    if (lastEmi) {
      return moment(lastEmi.emi_date).add(1, 'month').format('DD-MM-YYYY');
    } else {
      return 'No EMIs Paid';
    }
  };


  const calculateCurrentValue = (chit) => {
    const value = chit.value ?? 0;
    const duration = chit.duration ?? 1; // Assuming the duration should never be 0
    const emisPaid = chit.emis ? chit.emis.length : 0; // Get the number of EMIs paid

    return (emisPaid / duration) * value;
  };

   const totalCurrentValue = variableChits.reduce((total, chit) => total + calculateCurrentValue(chit), 0);



  return (
    <ChitContainer>
      <Header>Variable Chits</Header>
      <Button variant="contained" color="secondary" onClick={() => window.history.back()} >
                    Back to Chits Dashboard
                  </Button>
      <Button variant="contained" color="primary" onClick={handleOpen} style={{ marginLeft: '20px' }}>
        Add New Variable Chit
      </Button>
      <Grid container spacing={3} style={{ marginTop: '20px' }}>
        {variableChits.map((chit) => (
          <Grid item xs={12} sm={6} md={4} key={chit.chit_id}>
            <Widget>
              <h2>{chit.organisation}</h2>
              <p>Value: ₹{(chit.value ?? 0).toLocaleString()}</p>
              <p>Total Amount Paid: ₹{calculateTotalEmiPaid(chit.emis).toLocaleString()}</p>
              <p>Current Value: ₹{calculateCurrentValue(chit).toLocaleString()}</p>
              <p>Next EMI Date: {getNextEmiDate(chit.emis)}</p>
              <p>Duration: {chit.duration}</p>
              <p>Maturity Date: {chit.maturity}</p>
              <p>Started On: {chit.started}</p>
              <Button onClick={() => handleEdit(chit)}>Edit</Button>
              <Button onClick={() => handleDelete(chit.chit_id)}>Delete</Button>
              <Button onClick={() => handleAddEmi(chit)}>Add EMI</Button>
              <EmiTable>
                <h3>EMI Records:</h3>
                {chit.emis.map((emi) => (
                  <EmiRow key={emi.id}>
                    <span>EMI {emi.emi_no}:</span>
                    <span>₹{(emi.amount ?? 0).toLocaleString()}</span>
                    <span>{moment(emi.emi_date).format('DD-MM-YYYY')}</span>
                    <Button onClick={() => handleEditEmi(chit, emi)}>Edit</Button>
                    <Button onClick={() => handleDeleteEmi(chit.chit_id, emi.id)}>Delete</Button>
                  </EmiRow>
                ))}
              </EmiTable>
            </Widget>
          </Grid>
        ))}
      </Grid>

      {/* Chit Dialog */}
      <Dialog open={open} onClose={handleClose} fullWidth>
        <DialogTitle>{isEditing ? 'Edit Variable Chit' : 'Add Variable Chit'}</DialogTitle>
        <DialogContent>
          <ChitForm>
            <ChitItem>
              <TextField label="Organisation" name="organisation" value={formData.organisation} onChange={handleChange} fullWidth />
            </ChitItem>
            <ChitItem>
              <TextField label="Value" name="value" value={formData.value} onChange={handleChange} fullWidth />
            </ChitItem>
            <ChitItem>
              <TextField label="Duration" name="duration" value={formData.duration} onChange={handleChange} fullWidth />
            </ChitItem>
            <ChitItem>
              <TextField label="EMI" name="emi" value={formData.emi} onChange={handleChange} fullWidth />
            </ChitItem>
            <ChitItem>
              <TextField label="Maturity Date" name="maturity" value={formData.maturity} onChange={handleChange} fullWidth />
            </ChitItem>
            <ChitItem>
              <TextField label="Start Date" name="started" value={formData.started} onChange={handleChange} fullWidth />
            </ChitItem>
          </ChitForm>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button onClick={handleSubmit}>{isEditing ? 'Update' : 'Save'}</Button>
        </DialogActions>
      </Dialog>

      {/* EMI Dialog */}
      <Dialog open={openEmi} onClose={handleCloseEmi} fullWidth>
        <DialogTitle>{isEditingEmi ? 'Edit EMI' : 'Add EMI'}</DialogTitle>
        <DialogContent>
          <ChitForm>
            <ChitItem>
              <TextField label="EMI No" name="emi_no" value={emiFormData.emi_no} onChange={handleEmiChange} fullWidth />
            </ChitItem>
            <ChitItem>
              <TextField label="Amount" name="amount" value={emiFormData.amount} onChange={handleEmiChange} fullWidth />
            </ChitItem>
            <ChitItem>
              <TextField label="EMI Date" type="date" name="emi_date" value={emiFormData.emi_date} onChange={handleEmiChange} fullWidth />
            </ChitItem>
          </ChitForm>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseEmi}>Cancel</Button>
          <Button onClick={handleSubmitEmi}>{isEditingEmi ? 'Update' : 'Save'}</Button>
        </DialogActions>
      </Dialog>
      {/* Total Current Value Display */}
            <div style={{ textAlign: 'center', marginTop: '20px', color: 'white' }}>
              <h2>Total Value: ₹{totalCurrentValue}</h2>
            </div>

      <Snackbar open={notification.open} autoHideDuration={6000} onClose={handleNotificationClose}>
        <Alert onClose={handleNotificationClose} severity={notification.severity}>
          {notification.message}
        </Alert>
      </Snackbar>
    </ChitContainer>
  );
};

export default VariableChits;
