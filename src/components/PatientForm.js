import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
// import './PatientForm.css';

function api() {
  const instance = axios.create();
  instance.interceptors.request.use(cfg => {
    const token = localStorage.getItem('token');
    if (token) cfg.headers.Authorization = `Bearer ${token}`;
    return cfg;
  });
  return instance;
}

export default function PatientForm(){
  const [age, setAge] = useState('');
  const [symptoms, setSymptoms] = useState('');
  const [duration, setDuration] = useState('');
  const [allergies, setAllergies] = useState('');
  const [conditions, setConditions] = useState('');

  const [assessment, setAssessment] = useState(null);
  const [loading, setLoading] = useState(false);
  const [desiredDate, setDesiredDate] = useState('');
  const [notes, setNotes] = useState('');
  const [appointmentResponse, setAppointmentResponse] = useState(null);

  const [draftSavedAt, setDraftSavedAt] = useState(null);

  // load draft + last assessment from localStorage on mount
  useEffect(()=>{
    try{
      const draftRaw = localStorage.getItem('patient_form_draft');
      if(draftRaw){
        const d = JSON.parse(draftRaw);
        if(d.age) setAge(d.age);
        if(d.symptoms) setSymptoms(d.symptoms);
        if(d.duration) setDuration(d.duration);
        if(d.allergies) setAllergies(d.allergies);
        if(d.conditions) setConditions(d.conditions);
        if(d.desiredDate) setDesiredDate(d.desiredDate);
        if(d.notes) setNotes(d.notes);
        if(d.assessment) setAssessment(d.assessment);
        if(d.savedAt) setDraftSavedAt(d.savedAt);
      }
    }catch(e){/* ignore */}

    // also restore last_assessment if present
    try{
      const last = localStorage.getItem('last_assessment');
      if(last){ setAssessment(JSON.parse(last)); }
    }catch(e){}
  }, []);

  function saveDraft(extra = {}){
    try{
      const obj = {
        age, symptoms, duration, allergies, conditions, desiredDate, notes, assessment,
        savedAt: (new Date()).toISOString(),
        ...extra
      };
      localStorage.setItem('patient_form_draft', JSON.stringify(obj));
      setDraftSavedAt(obj.savedAt);
    }catch(e){/*ignore*/}
  }

  // auto-save when relevant fields change
  useEffect(()=>{
    saveDraft();
  }, [age, symptoms, duration, allergies, conditions, desiredDate, notes, assessment]);

  const desiredDateRef = React.createRef();

  function extractMeds(adviceText, symptomsText){
    const known = [
      'paracetamol','acetaminophen','ibuprofen','naproxen','naproxen sodium',
      'antihistamine','loratadine','cetirizine','diphenhydramine','chlorpheniramine',
      'decongestant','pseudoephedrine','phenylephrine','oxymetazoline',
      'dextromethorphan','guaifenesin','saline','honey','lozenge','menthol',
      'hydrocortisone','bacitracin','neomycin','calamine','loperamide','bismuth','antacid','oral rehydration',
      'nausea','vomit','vomiting','dimenhydrinate','meclizine','senna','polyethylene glycol','docusate','bisacodyl','laxative'
    ];

    const lower = (adviceText||'').toLowerCase();
    let found = known.filter(k=> lower.includes(k));
    if(found.length) return Array.from(new Set(found.map(f=>f)));

    // fallback suggestions based on symptoms
    const s = (symptomsText||'').toLowerCase();
    const suggestions = new Set();

    // Fever / pain
    if(s.match(/\b(fever|headache|pain|ache|muscle)\b/)){
      suggestions.add('paracetamol (acetaminophen)');
      suggestions.add('ibuprofen (if no contraindication)');
      suggestions.add('naproxen sodium (if appropriate)');
    }

    // Cough
    if(s.includes('cough')){
      suggestions.add('dextromethorphan (cough suppressant - for dry cough)');
      suggestions.add('guaifenesin (expectorant - for productive cough)');
      suggestions.add('honey or throat lozenges (children >1y for cough relief)');
    }

    // Nasal congestion / runny nose / sneezing
    if(s.includes('congest')||s.includes('runny')||s.includes('sneeze')||s.includes('nasal')){
      suggestions.add('saline nasal spray');
      suggestions.add('oxymetazoline nasal spray (short-term use)');
      suggestions.add('oral decongestant (pseudoephedrine or phenylephrine) — check interactions');
    }

    // Allergies / hayfever / itch
    if(s.includes('allerg')||s.includes('itch')||s.includes('hayfever')||s.includes('sneez')){
      suggestions.add('loratadine or cetirizine (non-drowsy antihistamines)');
      suggestions.add('diphenhydramine (sedating antihistamine - avoid if you must stay alert)');
    }

    // Skin issues (rash, minor wound)
    if(s.includes('rash')||s.includes('hives')||s.includes('skin')||s.includes('wound')){
      suggestions.add('topical hydrocortisone 1% cream for mild inflammation');
      suggestions.add('antiseptic/antibiotic ointment (e.g., bacitracin/neosporin) for minor wounds');
      suggestions.add('calamine lotion for itch or mild rash');
    }

    // Gastrointestinal - diarrhea, nausea, vomiting, constipation
    if(s.includes('diarrh')||s.includes('diarrhoea')||s.includes('loose stool')){
      suggestions.add('loperamide for diarrhea (follow dosing instructions)');
      suggestions.add('oral rehydration salts to prevent dehydration');
    }
    if(s.includes('nausea')||s.includes('nauseous')){
      suggestions.add('oral rehydration and small, bland meals; see pharmacist for anti-nausea options');
      suggestions.add('dimenhydrinate or meclizine (for motion sickness/vertigo - check with pharmacist)');
    }
    if(s.includes('vomit')||s.includes('vomiting')){
      suggestions.add('small sips of oral rehydration; seek pharmacist advice for antiemetics (dimenhydrinate/meclizine)');
    }
    if(s.includes('constip')||s.includes('constipation')||s.includes('hard stool')){
      suggestions.add('increase dietary fiber and fluids; consider bulk-forming fiber or polyethylene glycol (osmotic laxative)');
      suggestions.add('short-term stimulant laxatives (senna, bisacodyl) or stool softeners (docusate) if required - check with pharmacist');
    }

    if(s.includes('heartburn')||s.includes('acid')||s.includes('reflux')){
      suggestions.add('antacids (calcium carbonate) or H2 blockers - check with pharmacist for persistent symptoms');
    }

    if(suggestions.size) return Array.from(suggestions);

    // default fallbacks
    return ['paracetamol (acetaminophen)', 'ibuprofen (if no contraindication)', 'saline nasal spray', 'lozenges or throat soothing options'];
  }

  async function assess(){
    if(!symptoms) return alert('Please enter symptoms');
    setLoading(true);
    setAssessment(null);
    setAppointmentResponse(null);
    try{
      const res = await api().post('/api/chat/assess', { age, symptoms, duration, allergies, conditions });
      const ass = { id: res.data.assessment_id, severity: res.data.severity, advice: res.data.advice, suggested_meds: res.data.suggested_meds || [], model_meds_raw: res.data.model_meds_raw || '' };
      setAssessment(ass);
      // persist the assessment so it survives refresh
      try{ localStorage.setItem('last_assessment', JSON.stringify(ass)); }catch(e){}
      saveDraft();

      // if urgent or critical, focus appointment input
      if(['critical','urgent'].includes(ass.severity)){
        setTimeout(()=>{ try{ desiredDateRef.current?.focus(); }catch(e){} }, 200);
      }

    }catch(err){
      alert('Assessment failed: ' + (err.response?.data?.error || err.message));
    }finally{ setLoading(false); }
  }

  const [apptSubmitting, setApptSubmitting] = useState(false);

  async function submitAppointment(){
    if(!assessment) return alert('No assessment available');
    if(!['critical','urgent'].includes(assessment.severity)) return alert('Only serious assessments can request appointments');
    setApptSubmitting(true);
    try{
      const res = await api().post('/api/chat/appointments', { assessment_id: assessment.id, desired_date: desiredDate, notes });
      setAppointmentResponse({ success: true, appointment_id: res.data.appointment_id });
      // clear saved draft after a successful request
      try{ localStorage.removeItem('patient_form_draft'); }catch(e){}
      setDraftSavedAt(null);
    }catch(err){
      const status = err.response?.status;
      const msg = err.response?.data?.error || err.message;
      if(status === 404){
        alert('Appointment failed: assessment not found. Please re-run the assessment (Assess) before requesting an appointment.');
      }else if(status === 403){
        alert('Appointment failed: only serious assessments can request appointments. Please follow the advice or reassess.');
      }else{
        alert('Appointment failed: ' + msg);
      }
      setAppointmentResponse({ success: false, error: msg });
    }finally{ setApptSubmitting(false); }
  }

  return (
    <div className="container mt-4">
      <div className="d-flex justify-content-between align-items-center">
        <h3>Patient Condition Form</h3>
        <div>
          <Link to="/chat" className="btn btn-secondary me-2">Go to Chat</Link>
        </div>
      </div>

      <div className="card mt-3 p-3">
        <div className="row">
          <div className="col-md-2 mb-2">
            <input className="form-control" placeholder="Age" value={age} onChange={(e)=>setAge(e.target.value)} />
          </div>
          <div className="col-md-4 mb-2">
            <input className="form-control" placeholder="Duration (days)" value={duration} onChange={(e)=>setDuration(e.target.value)} />
          </div>

        </div>
        <div className="mb-2">
          <textarea className="form-control" placeholder="Key symptoms" value={symptoms} onChange={(e)=>setSymptoms(e.target.value)} rows={2}></textarea>
        </div>
        <div className="row">
          <div className="col-md-6 mb-2">
            <input className="form-control" placeholder="Allergies" value={allergies} onChange={(e)=>setAllergies(e.target.value)} />
          </div>
          <div className="col-md-6 mb-2">
            <input className="form-control" placeholder="Major conditions" value={conditions} onChange={(e)=>setConditions(e.target.value)} />
          </div>
        </div>
        <div className="d-flex gap-2 align-items-center">
          <button className="btn btn-primary" onClick={assess} disabled={loading}>{loading ? 'Assessing...' : 'Assess'}</button>
          {draftSavedAt && <small className="text-muted ms-3">Draft saved: {new Date(draftSavedAt).toLocaleString()}</small>}
        </div>

        {assessment && (
          <div className="mt-3 p-2 border rounded bg-light">
            <strong>Severity:</strong> <span className="me-3">{assessment.severity}</span>
            <div className="mt-2"><strong>Advice:</strong><div className="mt-1">{assessment.advice}</div></div>

            {['critical','urgent'].includes(assessment.severity) && (
              <div className="mt-3">
                <h6>Request an appointment</h6>
                <div className="row">
                  <div className="col-md-4 mb-2">
                    <input ref={desiredDateRef} className="form-control" type="datetime-local" value={desiredDate} onChange={(e)=>setDesiredDate(e.target.value)} />
                  </div>
                  <div className="col-md-8 mb-2">
                    <input className="form-control" placeholder="Notes for the doctor" value={notes} onChange={(e)=>setNotes(e.target.value)} />
                  </div>
                </div>
                <div className="d-flex gap-2">
                  <button className="btn btn-success" onClick={submitAppointment} disabled={apptSubmitting}>{apptSubmitting ? 'Submitting...' : 'Submit appointment request'}</button>
                </div>

                {appointmentResponse && (
                  <div className="mt-2">
                    {appointmentResponse.success ? (
                      <div className="alert alert-success">Appointment requested (id: {appointmentResponse.appointment_id})</div>
                    ) : (
                      <div className="alert alert-danger">Error: {appointmentResponse.error}</div>
                    )}
                  </div>
                )}
              </div>
            )}

            {assessment && assessment.severity === 'non_urgent' && (
              <div className="mt-3 p-2 border rounded bg-light">
                <h6>Suggested OTC options</h6>
                <p className="mb-1">These are common, non-prescription options for symptoms — consult a pharmacist if you have allergies or other medications.</p>

                {assessment.suggested_meds && assessment.suggested_meds.length > 0 ? (
                  <ul>
                    {assessment.suggested_meds.map((m,i)=> <li key={i}><strong>{m}</strong></li>)}
                  </ul>
                ) : (
                  <ul>
                    {extractMeds(assessment.advice, symptoms).map((m,i)=> <li key={i}>{m}</li>)}
                  </ul>
                )}

                <div className="d-flex gap-2">
                  <button className="btn btn-sm btn-outline-primary" onClick={()=>{ const list = (assessment.suggested_meds && assessment.suggested_meds.length>0) ? assessment.suggested_meds.join(', ') : extractMeds(assessment.advice, symptoms).join(', '); navigator.clipboard?.writeText(list); alert('Copied suggestions'); }}>Copy suggestions</button>
                </div>

                {assessment.model_meds_raw && (
                  <div className="mt-2 text-muted"><small><strong>Model raw suggestions:</strong> {assessment.model_meds_raw}</small></div>
                )}

                <div className="mt-2 text-warning"><small><strong>Note:</strong> These are suggestions only — not prescriptions. Consult your doctor or pharmacist before taking any medicine.</small></div>
              </div>
            )}

          </div>
        )}
      </div>
    </div>
  )
}