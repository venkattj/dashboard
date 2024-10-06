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
        await api.put(`/api/variable_chits/${currentChit.chit_id}`, formData);
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
      await api.delete(`/api/variable_chits/${chit_id}`);
      setNotification({ open: true, message: 'Variable chit deleted successfully!', severity: 'success' });
      fetchVariableChits();
    } catch (error) {
      setNotification({ open: true, message: 'Error deleting variable chit!', severity: 'error' });
    }
  };

  // EMI CRUD Handlers
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

  return (
    <ChitContainer>
      <Header>Variable Chits</Header>
      <Button variant="contained" color="primary" onClick={handleOpen}>
        Add New Variable Chit
      </Button>
      <Grid container spacing={3} style={{ marginTop: '20px' }}>
        {variableChits.map((chit) => (
          <Grid item xs={12} sm={6} md={4} key={chit.chit_id}>
            <Widget>
              <h2>{chit.organisation}</h2>
              <p>Value: ₹{chit.value.toLocaleString()}</p>
              <p>Duration: {chit.duration} months</p>
              <p>Maturity Date: {moment(chit.maturity).format('DD-MM-YYYY')}</p>
              <p>Started On: {moment(chit.started).format('DD-MM-YYYY')}</p>
              <Button variant="outlined" color="secondary" onClick={() => handleEdit(chit)}>
                Edit
              </Button>
              <Button variant="outlined" color="error" onClick={() => handleDelete(chit.chit_id)}>
                Delete
              </Button>
              <EmiTable>
                <h3>EMIs</h3>
                {chit.emis.length > 0 ? (
                  chit.emis.map((emi) => (
                    <EmiRow key={emi.emi_no}>
                      <span>EMI {emi.emi_no}: ₹{emi.amount}</span>
                      <span>Date: {moment(emi.emi_date).format('DD-MM-YYYY')}</span>
                      <Button variant="outlined" onClick={() => handleEditEmi(chit, emi)}>
                        Edit EMI
                      </Button>
                      <Button variant="outlined" color="error" onClick={() => handleDeleteEmi(chit.chit_id, emi.id)}>
                        Delete EMI
                      </Button>
                    </EmiRow>
                  ))
                ) : (
                  <p>No EMIs found</p>
                )}
              </EmiTable>
              <Button variant="outlined" color="primary" onClick={() => handleAddEmi(chit)}>
                Add EMI
              </Button>
            </Widget>
          </Grid>
        ))}
      </Grid>

      {/* Chit Dialog */}
      <Dialog open={open} onClose={handleClose}>
        <DialogTitle>{isEditing ? 'Edit Variable Chit' : 'Add Variable Chit'}</DialogTitle>
        <DialogContent>
          <ChitForm>
            <ChitItem>
              <TextField
                label="Organisation"
                name="organisation"
                value={formData.organisation}
                onChange={handleChange}
                fullWidth
              />
            </ChitItem>
            <ChitItem>
              <TextField label="Value" name="value" type="number" value={formData.value} onChange={handleChange} fullWidth />
            </ChitItem>
            <ChitItem>
              <TextField label="Duration" name="duration" type="number" value={formData.duration} onChange={handleChange} fullWidth />
            </ChitItem>
            <ChitItem>
              <TextField label="Maturity" name="maturity" type="date" value={formData.maturity} onChange={handleChange} fullWidth />
            </ChitItem>
            <ChitItem>
              <TextField label="Started" name="started" type="date" value={formData.started} onChange={handleChange} fullWidth />
            </ChitItem>
          </ChitForm>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} color="secondary">
            Cancel
          </Button>
          <Button onClick={handleSubmit} color="primary">
            {isEditing ? 'Update' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* EMI Dialog */}
      <Dialog open={openEmi} onClose={handleCloseEmi}>
        <DialogTitle>{isEditingEmi ? 'Edit EMI' : 'Add EMI'}</DialogTitle>
        <DialogContent>
          <ChitForm>
            <ChitItem>
              <TextField
                label="EMI Number"
                name="emi_no"
                type="number"
                value={emiFormData.emi_no}
                onChange={handleEmiChange}
                fullWidth
              />
            </ChitItem>
            <ChitItem>
              <TextField label="Amount" name="amount" type="number" value={emiFormData.amount} onChange={handleEmiChange} fullWidth />
            </ChitItem>
            <ChitItem>
              <TextField label="EMI Date" name="emi_date" type="date" value={emiFormData.emi_date} onChange={handleEmiChange} fullWidth />
            </ChitItem>
          </ChitForm>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseEmi} color="secondary">
            Cancel
          </Button>
          <Button onClick={handleSubmitEmi} color="primary">
            {isEditingEmi ? 'Update' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar Notification */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleNotificationClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleNotificationClose} severity={notification.severity}>
          {notification.message}
        </Alert>
      </Snackbar>
    </ChitContainer>
  );
};

export default VariableChits;
