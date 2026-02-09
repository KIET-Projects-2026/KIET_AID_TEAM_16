import React, { useEffect, useState } from 'react';
import axios from 'axios';

function api(){
  const instance = axios.create();
  instance.interceptors.request.use(cfg=>{
    const token = localStorage.getItem('token');
    if(token) cfg.headers.Authorization = `Bearer ${token}`;
    return cfg;
  });
  return instance;
}

export default function DoctorDashboard(){
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showOnlyUrgent, setShowOnlyUrgent] = useState(true);

  async function load(){
    setLoading(true);
    try{
      const res = await api().get('/api/chat/appointments');
      let appts = res.data.appointments || [];
      if(showOnlyUrgent){
        appts = appts.filter(a => (a.assessment_snapshot && ['critical','urgent'].includes(a.assessment_snapshot.severity)));
      }
      setAppointments(appts);

      // if there are urgent appointments, auto-open the first one when doctor lands
      if(appts.length > 0){
        setTimeout(()=>{ try{ viewReport(appts[0]._id); }catch(e){} }, 200);
      }
    }catch(err){
      alert('Failed to load appointments: ' + (err.response?.data?.error||err.message));
    }finally{ setLoading(false); }
  }

  useEffect(()=>{ load(); },[showOnlyUrgent]);

  const [showReportFor, setShowReportFor] = useState(null);
  const [reportData, setReportData] = useState(null);

  const [doctorNote, setDoctorNote] = useState('');

  async function viewReport(apptId){
    try{
      const res = await api().get(`/api/chat/appointments/${apptId}`);
      const appt = res.data.appointment;
      // include patient info if present
      const snapshot = Object.assign({}, appt.assessment_snapshot || {});
      snapshot.patient_name = appt.patient_name || '';
      snapshot.patient_email = appt.patient_email || '';
      setReportData(snapshot || null);
      setShowReportFor(apptId);
    }catch(err){
      alert('Failed to fetch report: ' + (err.response?.data?.error||err.message));
    }
  }

  const [historyFor, setHistoryFor] = useState(null);
  const [historyData, setHistoryData] = useState(null);

  async function viewHistory(patientId){
    try{
      const res = await api().get(`/api/chat/patient/${patientId}/history`);
      setHistoryData(res.data.history || []);
      setHistoryFor(patientId);
    }catch(err){
      alert('Failed to fetch history: ' + (err.response?.data?.error||err.message));
    }
  }

  async function updateStatus(id, status, note=''){
    try{
      await api().put(`/api/chat/appointments/${id}/status`, { status, note });
      load();
      // if appointment accepted and doctor wrote a note, auto-open patient chat
      if(status === 'accepted' && note){
        alert('Appointment accepted and patient notified.');
      }
    }catch(err){
      alert('Update failed: ' + (err.response?.data?.error||err.message));
    }
  }

  return (
    <div className="container mt-4">
      <div className="d-flex justify-content-between align-items-center">
        <h3>Doctor Dashboard</h3>
        <div>
          <label className="me-2"><input type="checkbox" checked={showOnlyUrgent} onChange={(e)=>setShowOnlyUrgent(e.target.checked)} /> Show only urgent</label>
        </div>
      </div>
      <p>Pending appointments and requests from patients.</p>
      {loading ? <div>Loading...</div> : (
        <div>
          {appointments.length === 0 ? <div>No appointments</div> : (
            <table className="table table-sm">              <thead><tr><th>Id</th><th>Patient</th><th>Severity</th><th>Desired</th><th>Status</th><th>Actions</th></tr></thead>
              <tbody>
                {appointments.map(a => (
                  <tr key={a._id}>
                    <td>{a._id}</td>
                    <td>{a.patient_id}</td>
                    <td>{(a.assessment_snapshot && a.assessment_snapshot.severity) || (a.assessment_id && 'see') || ''}</td>
                    <td>{a.desired_date || '-'}</td>
                    <td>{a.status}</td>
                    <td>
                      <button className="btn btn-sm btn-info me-1" onClick={()=>viewReport(a._id)}>View Report</button>
                      <button className="btn btn-sm btn-outline-secondary me-1" onClick={()=>viewHistory(a.patient_id)}>View History</button>
                      <button className="btn btn-sm btn-success me-1" onClick={()=>updateStatus(a._id, 'accepted')}>Accept</button>
                      <button className="btn btn-sm btn-danger" onClick={()=>updateStatus(a._id, 'declined')}>Decline</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {showReportFor && reportData && (
            <div className="card mt-3 p-3">
              <h5>Assessment Report (Appointment: {showReportFor})</h5>
              <div><strong>Patient:</strong> {reportData.patient_name || reportData.patient_email || 'Unknown'}</div>
              <div><strong>Severity:</strong> {reportData.severity}</div>
              <div className="mt-2"><strong>Form:</strong>
                <ul>
                  <li><strong>Age:</strong> {reportData.form?.age || '-'}</li>
                  <li><strong>Symptoms:</strong> {reportData.form?.symptoms || '-'}</li>
                  <li><strong>Duration:</strong> {reportData.form?.duration || '-'}</li>

                  <li><strong>Allergies:</strong> {reportData.form?.allergies || '-'}</li>
                  <li><strong>Conditions:</strong> {reportData.form?.conditions || '-'}</li>
                </ul>
              </div>
              <div className="mt-2"><strong>Advice:</strong><div>{reportData.advice}</div></div>

              <div className="mt-3">
                <label className="form-label">Doctor note</label>
                <textarea className="form-control mb-2" value={doctorNote} onChange={(e)=>setDoctorNote(e.target.value)} rows={3} placeholder="Enter a note for patient or appointment details"></textarea>
                <div className="d-flex gap-2">
                  <button className="btn btn-sm btn-success" onClick={()=>{ updateStatus(showReportFor, 'accepted', doctorNote); setDoctorNote(''); }}>Accept & Send Note</button>
                  <button className="btn btn-sm btn-danger" onClick={()=>{ updateStatus(showReportFor, 'declined', doctorNote); setDoctorNote(''); }}>Decline</button>
                  <button className="btn btn-sm btn-secondary" onClick={()=>{ setShowReportFor(null); setReportData(null); }}>Close</button>
                </div>
              </div>
            </div>
          )}

          {historyFor && historyData && (
            <div className="card mt-3 p-3">
              <h5>Patient History ({historyFor})</h5>
              {historyData.length === 0 ? <div>No history</div> : (
                <ul>
                  {historyData.map(h => (
                    <li key={h._id}>{h.type || h.from_role || 'entry'} — {h.answer || JSON.stringify(h.form)||''} <small className="text-muted">{h.created_at || ''}</small></li>
                  ))}
                </ul>
              )}
              <div className="mt-3"><button className="btn btn-sm btn-secondary" onClick={()=>{ setHistoryFor(null); setHistoryData(null); }}>Close</button></div>
            </div>
          )}

        </div>
      )}
    </div>
  )
}