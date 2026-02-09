from flask import Blueprint, request, jsonify, g
from utils.model_loader import generate_answer
from db.mongo import chats, users, appointments
from utils.auth import require_auth, require_role
from bson.objectid import ObjectId
from datetime import datetime
import logging

log = logging.getLogger(__name__)
chat_bp = Blueprint("chat", __name__)

RED_FLAGS = [
    'chest pain', 'shortness of breath', 'difficulty breathing', 'fainting',
    'loss of consciousness', 'slurred speech', 'sudden weakness', 'severe bleeding',
    'severe allergic reaction', 'severe abdominal pain', 'seizure'
]

# Comprehensive medicine database with uses, dosages, and precautions
MEDICINE_DATABASE = {
    # Pain & Fever Relief
    'paracetamol': {
        'uses': ['fever', 'headache', 'body ache', 'pain'],
        'dosage': '500-1000 mg every 4-6 hours',
        'max_daily': '3000-4000 mg',
        'side_effects': ['nausea', 'headache'],
        'precautions': ['liver disease', 'alcohol use'],
        'category': 'pain_relief'
    },
    'acetaminophen': {
        'uses': ['fever', 'headache', 'body ache', 'pain'],
        'dosage': '500-1000 mg every 4-6 hours',
        'max_daily': '3000-4000 mg',
        'side_effects': ['nausea', 'headache'],
        'precautions': ['liver disease', 'alcohol use'],
        'category': 'pain_relief'
    },
    'ibuprofen': {
        'uses': ['fever', 'headache', 'body ache', 'pain', 'inflammation', 'joint pain'],
        'dosage': '200-400 mg every 4-6 hours',
        'max_daily': '1200-1600 mg',
        'side_effects': ['nausea', 'stomach upset', 'dizziness'],
        'precautions': ['stomach ulcers', 'kidney disease', 'heart disease'],
        'category': 'pain_relief'
    },
    'aspirin': {
        'uses': ['headache', 'pain', 'fever'],
        'dosage': '325-650 mg every 4-6 hours',
        'max_daily': '3000-4000 mg',
        'side_effects': ['stomach upset', 'nausea'],
        'precautions': ['bleeding disorders', 'asthma', 'stomach ulcers'],
        'category': 'pain_relief'
    },

    # Cough & Cold
    'dextromethorphan': {
        'uses': ['dry cough', 'persistent cough'],
        'dosage': '10-20 mg every 4 hours',
        'max_daily': '120 mg',
        'side_effects': ['dizziness', 'drowsiness'],
        'precautions': ['asthma', 'pregnancy'],
        'category': 'cough'
    },
    'guaifenesin': {
        'uses': ['cough with mucus', 'phlegm', 'wet cough'],
        'dosage': '200-400 mg every 4 hours',
        'max_daily': '2400 mg',
        'side_effects': ['nausea', 'vomiting'],
        'precautions': ['kidney disease'],
        'category': 'cough'
    },
    'pseudoephedrine': {
        'uses': ['nasal congestion', 'stuffy nose', 'sinus congestion'],
        'dosage': '30-60 mg every 4-6 hours',
        'max_daily': '240 mg',
        'side_effects': ['insomnia', 'nervousness', 'headache'],
        'precautions': ['heart disease', 'high blood pressure', 'diabetes'],
        'category': 'decongestant'
    },
    'phenylephrine': {
        'uses': ['nasal congestion', 'stuffy nose'],
        'dosage': '10 mg every 4 hours',
        'max_daily': '60 mg',
        'side_effects': ['nervousness', 'insomnia'],
        'precautions': ['heart disease', 'high blood pressure'],
        'category': 'decongestant'
    },

    # Allergy
    'cetirizine': {
        'uses': ['allergies', 'itching', 'hives', 'runny nose', 'sneezing'],
        'dosage': '5-10 mg once daily',
        'max_daily': '10 mg',
        'side_effects': ['drowsiness', 'headache'],
        'precautions': ['kidney disease'],
        'category': 'antihistamine'
    },
    'loratadine': {
        'uses': ['allergies', 'itching', 'hives', 'runny nose'],
        'dosage': '10 mg once daily',
        'max_daily': '10 mg',
        'side_effects': ['headache', 'drowsiness'],
        'precautions': ['kidney disease', 'liver disease'],
        'category': 'antihistamine'
    },
    'diphenhydramine': {
        'uses': ['allergies', 'itching', 'hives', 'sleep'],
        'dosage': '25-50 mg every 4-6 hours',
        'max_daily': '300 mg',
        'side_effects': ['drowsiness', 'dizziness'],
        'precautions': ['driving', 'pregnancy'],
        'category': 'antihistamine'
    },

    # Topical/Natural
    'saline nasal spray': {
        'uses': ['nasal congestion', 'stuffy nose', 'post-nasal drip'],
        'dosage': 'spray as needed',
        'max_daily': 'unlimited',
        'side_effects': [],
        'precautions': [],
        'category': 'topical'
    },
    'honey': {
        'uses': ['cough', 'sore throat', 'throat irritation'],
        'dosage': '1-2 teaspoons',
        'max_daily': 'as needed',
        'side_effects': [],
        'precautions': ['infants under 1 year'],
        'category': 'natural'
    },
    'menthol': {
        'uses': ['cough', 'congestion', 'muscle ache'],
        'dosage': 'topical as needed',
        'max_daily': 'as needed',
        'side_effects': [],
        'precautions': ['sensitive skin'],
        'category': 'topical'
    },

    # Prescription (informational only)
    'levothyroxine': {
        'uses': ['hypothyroidism', 'thyroid'],
        'dosage': 'varies (typically 25-200 mcg daily)',
        'max_daily': 'varies',
        'side_effects': ['tremor', 'anxiety', 'headache'],
        'precautions': ['heart disease', 'pregnancy'],
        'category': 'prescription'
    },
    'atorvastatin': {
        'uses': ['high cholesterol', 'heart disease prevention'],
        'dosage': '10-80 mg daily',
        'max_daily': '80 mg',
        'side_effects': ['muscle pain', 'weakness'],
        'precautions': ['liver disease', 'pregnancy'],
        'category': 'prescription'
    },
    'omeprazole': {
        'uses': ['acid reflux', 'heartburn', 'GERD', 'stomach ulcer'],
        'dosage': '20-40 mg daily',
        'max_daily': '40 mg',
        'side_effects': ['headache', 'nausea', 'abdominal pain'],
        'precautions': ['long-term use risks', 'magnesium deficiency'],
        'category': 'prescription'
    },
    'albuterol': {
        'uses': ['asthma', 'shortness of breath', 'breathing'],
        'dosage': '1-2 puffs every 4-6 hours as needed',
        'max_daily': 'varies',
        'side_effects': ['tremor', 'nervousness', 'headache'],
        'precautions': ['heart conditions'],
        'category': 'prescription'
    },
    'amoxicillin': {
        'uses': ['bacterial infection', 'strep throat', 'ear infection'],
        'dosage': '250-500 mg every 8 hours',
        'max_daily': '3000 mg',
        'side_effects': ['nausea', 'vomiting', 'rash'],
        'precautions': ['penicillin allergy'],
        'category': 'prescription'
    },
    'lisinopril': {
        'uses': ['high blood pressure', 'hypertension', 'heart failure'],
        'dosage': '10-40 mg daily',
        'max_daily': '80 mg',
        'side_effects': ['dizziness', 'headache', 'dry cough'],
        'precautions': ['kidney disease', 'pregnancy'],
        'category': 'prescription'
    },
}

# Simple whitelist of common safe OTC medicines
MEDICATION_WHITELIST = set(MEDICINE_DATABASE.keys())

def _normalize_med_name(name: str) -> str:
    return name.strip().lower().replace('.', '')

def _extract_valid_meds(text: str):
    """Extract candidate medicine names from text and intersect with whitelist."""
    if not text:
        return []
    candidates = []
    # naive split on commas and semicolons
    for part in [p.strip() for p in text.replace(';', ',').split(',') if p.strip()]:
        # take first token words
        token = part.split('(')[0].strip()
        token_norm = _normalize_med_name(token)
        # check direct or contains
        for w in MEDICATION_WHITELIST:
            if w in token_norm or token_norm in w:
                candidates.append(w)
    # preserve order, unique
    seen = set()
    out = []
    for c in candidates:
        if c not in seen:
            out.append(c)
            seen.add(c)
    return out


def _get_medicine_info(medicine_name: str) -> dict:
    """Get detailed information about a medicine."""
    med_norm = _normalize_med_name(medicine_name)
    if med_norm in MEDICINE_DATABASE:
        return MEDICINE_DATABASE[med_norm]
    return None


def _format_medicine_recommendation(medicine_name: str) -> str:
    """Format medicine information for display."""
    info = _get_medicine_info(medicine_name)
    if not info:
        return None
    
    med_norm = _normalize_med_name(medicine_name)
    output = f"\n**{med_norm.title()}**\n"
    output += f"  • Uses: {', '.join(info['uses'])}\n"
    output += f"  • Dosage: {info['dosage']}\n"
    if info['max_daily']:
        output += f"  • Max Daily: {info['max_daily']}\n"
    if info['precautions']:
        output += f"  • Precautions: {', '.join(info['precautions'])}\n"
    if info['side_effects']:
        output += f"  • Possible Side Effects: {', '.join(info['side_effects'])}\n"
    return output


def assess_severity(age, symptoms, duration, allergies, conditions):
    text = ' '.join([str(symptoms), str(conditions)]).lower()
    for rf in RED_FLAGS:
        if rf in text:
            return 'critical'

    if 'fever' in text and (age and int(age) < 2 if str(age).isdigit() else False):
        return 'urgent'

    try:
        d = int(duration)
        if d >= 7:
            return 'urgent'
    except Exception:
        pass

    return 'non_urgent'


@chat_bp.route("/ask", methods=["POST"])
@require_auth
def ask():
    data = request.json
    question = data.get("question")
    if not question:
        return jsonify({"error": "question required"}), 400

    # Use authenticated user id and role
    user_id = g.user_id
    role = g.role or 'patient'

    # Optional context fields (e.g., current medications, symptoms)
    context = data.get('context', {})

    answer = generate_answer(question, role=role, context=context)

    res = chats.insert_one({
        "user_id": user_id,
        "question": question,
        "answer": answer,
        "from_role": "system",
        "context": context,
        "timestamp": datetime.utcnow()
    })

    inserted_id = str(res.inserted_id)
    return jsonify({"answer": answer, "message_id": inserted_id})


@chat_bp.route('/history', methods=['GET'])
@require_auth
def history():
    user_id = g.user_id
    docs = list(chats.find({'user_id': user_id}).sort('timestamp', 1))
    for d in docs:
        d['_id'] = str(d['_id'])
        if 'timestamp' in d and hasattr(d['timestamp'], 'isoformat'):
            d['timestamp'] = d['timestamp'].isoformat()
    return jsonify({'history': docs})


# Assessment endpoint: accepts patient condition form, returns advice + severity
@chat_bp.route('/assess', methods=['POST'])
@require_auth
def assess():
    data = request.json or {}
    age = data.get('age')
    symptoms = data.get('symptoms') or ''
    duration = data.get('duration') or ''
    allergies = data.get('allergies') or ''
    conditions = data.get('conditions') or ''

    if not symptoms:
        return jsonify({'error': 'symptoms required'}), 400

    # assess without relying on meds field
    severity = assess_severity(age, symptoms, duration, allergies, conditions)

    prompt = (
        f"You are an experienced medical information specialist. A patient reports the following:\n\n"
        f"Age: {age}\n"
        f"Symptoms: {symptoms}\n"
        f"Duration: {duration}\n"
        f"Allergies: {allergies}\n"
        f"Medical History: {conditions}\n\n"
        f"Severity Assessment: {severity}\n\n"
        f"Please provide:\n"
        f"1. Initial assessment of symptoms\n"
        f"2. Specific home care recommendations (with details)\n"
        f"3. Safe over-the-counter options if appropriate\n"
        f"4. Clear warning signs that require medical attention\n"
        f"5. When to seek urgent care\n\n"
        f"Be thorough, practical, and safety-conscious. Highlight any red flags."
    )

    advice = generate_answer(prompt, role='patient', context={
        'symptoms': symptoms,
        'conditions': conditions,
        'allergies': allergies,
        'age': age
    })

    # Ask the trained model to list medicine suggestions (short list)
    meds_prompt = (
        f"Based on the reported symptoms ({symptoms}), medical history ({conditions}), and allergies ({allergies}), "
        "provide ONLY a brief comma-separated list of generic medication names that would be appropriate and safe. "
        "Focus on common OTC options. Do not include dosing, brand names, or controlled substances. "
        "If no medications are appropriate, respond with: 'None recommended at this time.' "
        "Example format: 'acetaminophen, ibuprofen (if no contraindication)'"
    )
    meds_raw = generate_answer(meds_prompt, role='patient', context={
        'symptoms': symptoms,
        'conditions': conditions,
        'allergies': allergies
    })
    validated_meds = _extract_valid_meds(meds_raw)

    # Generate detailed medicine information
    medicine_details = {}
    for med in validated_meds:
        med_info = _get_medicine_info(med)
        if med_info:
            medicine_details[med] = med_info

    assessment_doc = {
        'user_id': g.user_id,
        'type': 'assessment',
        'form': {
            'age': age,
            'symptoms': symptoms,
            'duration': duration,
            'allergies': allergies,
            'conditions': conditions
        },
        'severity': severity,
        'advice': advice,
        'model_meds_raw': meds_raw,
        'suggested_meds': validated_meds,
        'medicine_details': medicine_details,
        'created_at': datetime.utcnow()
    }

    res = chats.insert_one(assessment_doc)
    assessment_id = str(res.inserted_id)

    return jsonify({
        'assessment_id': assessment_id,
        'severity': severity,
        'advice': advice,
        'suggested_meds': validated_meds,
        'medicine_details': medicine_details,
        'model_meds_raw': meds_raw
    })


# Patient creates appointment request only for serious assessments
@chat_bp.route('/appointments', methods=['POST'])
@require_auth
def create_appointment():
    data = request.json or {}
    assessment_id = data.get('assessment_id')
    desired_date = data.get('desired_date')
    notes = data.get('notes', '')

    if not assessment_id:
        return jsonify({'error': 'assessment_id required'}), 400

    try:
        a = chats.find_one({'_id': ObjectId(assessment_id), 'user_id': g.user_id, 'type': 'assessment'})
    except Exception:
        return jsonify({'error': 'invalid assessment id'}), 400

    if not a:
        # More helpful error to guide user to re-run assessment if the assessment is missing or owned by another account
        return jsonify({'error': 'Assessment not found or not owned by the current user. Please re-run the assessment and try again.'}), 404

    if a.get('severity') not in ('critical', 'urgent'):
        return jsonify({'error': 'Only serious assessments can request appointments'}), 403

    # include a snapshot of the assessment (form, severity, advice) so doctors can see the report later
    assessment_snapshot = {
        'form': a.get('form', {}),
        'severity': a.get('severity'),
        'advice': a.get('advice'),
        'assessment_id': assessment_id
    }

    appt = {
        'patient_id': g.user_id,
        'assessment_id': assessment_id,
        'assessment_snapshot': assessment_snapshot,
        'desired_date': desired_date,
        'notes': notes,
        'status': 'pending',
        'created_at': datetime.utcnow()
    }

    r = appointments.insert_one(appt)
    appt_id = str(r.inserted_id)
    log.info(f"Appointment created {appt_id} for patient {g.user_id} severity={assessment_snapshot.get('severity')}")
    return jsonify({'appointment_id': appt_id, 'status': 'pending'})


@chat_bp.route('/appointments', methods=['GET'])
@require_auth
@require_role('doctor')
def list_appointments():
    docs = list(appointments.find())
    enriched = []
    for d in docs:
        # attach patient name/email when available
        patient_id = d.get('patient_id')
        patient_info = None
        try:
            if patient_id:
                patient_info = users.find_one({'_id': ObjectId(patient_id)}, {'password': 0})
        except Exception:
            patient_info = None
        if patient_info:
            d['patient_name'] = patient_info.get('name')
            d['patient_email'] = patient_info.get('email')
        d['_id'] = str(d['_id'])
        d['created_at'] = d.get('created_at').isoformat() if d.get('created_at') else None
        enriched.append(d)
    return jsonify({'appointments': enriched})


@chat_bp.route('/appointments/<appointment_id>', methods=['GET'])
@require_auth
@require_role('doctor')
def get_appointment(appointment_id):
    try:
        a = appointments.find_one({'_id': ObjectId(appointment_id)})
    except Exception:
        return jsonify({'error': 'invalid id'}), 400
    if not a:
        return jsonify({'error': 'Not found'}), 404
    # if appointment was created before snapshot was stored, try to fetch assessment
    if 'assessment_snapshot' not in a and a.get('assessment_id'):
        try:
            ass = chats.find_one({'_id': ObjectId(a['assessment_id']), 'type': 'assessment'})
            if ass:
                a['assessment_snapshot'] = {
                    'form': ass.get('form', {}),
                    'severity': ass.get('severity'),
                    'advice': ass.get('advice'),
                    'assessment_id': a.get('assessment_id')
                }
        except Exception:
            pass
    # attach patient name/email when available
    try:
        patient = users.find_one({'_id': ObjectId(a['patient_id'])}, {'password': 0}) if a.get('patient_id') else None
        if patient:
            a['patient_name'] = patient.get('name')
            a['patient_email'] = patient.get('email')
    except Exception:
        pass
    # convert datetimes to isoformat for JSON
    if 'created_at' in a and hasattr(a['created_at'], 'isoformat'):
        a['created_at'] = a['created_at'].isoformat()
    if 'assessment_snapshot' in a:
        # nothing else to do; assessment snapshot contains plain data
        pass
    a['_id'] = str(a['_id'])
    return jsonify({'appointment': a})


@chat_bp.route('/appointments/<appointment_id>/status', methods=['PUT'])
@require_auth
@require_role('doctor')
def update_appointment_status(appointment_id):
    data = request.json or {}
    status = data.get('status')
    note = data.get('note', '')

    if status not in ('accepted', 'declined'):
        return jsonify({'error': 'invalid status'}), 400

    try:
        r = appointments.update_one({'_id': ObjectId(appointment_id)}, {'$set': {'status': status, 'note': note, 'updated_at': datetime.utcnow()}})
    except Exception:
        return jsonify({'error': 'invalid id'}), 400

    if r.matched_count == 0:
        return jsonify({'error': 'Not found'}), 404

    # if accepted, also add a chat entry so patient can see doctor's note
    if status == 'accepted' and note:
        appt = appointments.find_one({'_id': ObjectId(appointment_id)})
        if appt:
            chats.insert_one({
                'user_id': appt['patient_id'],
                'question': None,
                'answer': f"Appointment update: {note}",
                'from_role': 'doctor',
                'doctor_id': g.user_id,
                'timestamp': datetime.utcnow()
            })

    return jsonify({'message': 'updated'})


# Doctor endpoints
@chat_bp.route('/patient/<patient_id>/history', methods=['GET'])
@require_auth
@require_role('doctor')
def patient_history(patient_id):
    docs = list(chats.find({'user_id': patient_id}).sort('timestamp', 1))
    for d in docs:
        d['_id'] = str(d['_id'])
        if 'timestamp' in d and hasattr(d['timestamp'], 'isoformat'):
            d['timestamp'] = d['timestamp'].isoformat()
    return jsonify({'history': docs})


@chat_bp.route('/assessments/<assessment_id>', methods=['GET'])
@require_auth
def get_assessment(assessment_id):
    try:
        ass = chats.find_one({'_id': ObjectId(assessment_id), 'type': 'assessment'})
    except Exception:
        return jsonify({'error': 'invalid id'}), 400
    if not ass:
        return jsonify({'error': 'Not found'}), 404
    # allow patients to view their own assessment or doctors to view any
    if g.role != 'doctor' and str(ass.get('user_id')) != g.user_id:
        return jsonify({'error': 'Forbidden'}), 403
    ass['_id'] = str(ass['_id'])
    if 'created_at' in ass and hasattr(ass['created_at'], 'isoformat'):
        ass['created_at'] = ass['created_at'].isoformat()
    return jsonify({'assessment': ass})

@chat_bp.route('/patient/<patient_id>/suggest', methods=['POST'])
@require_auth
@require_role('doctor')
def patient_suggest(patient_id):
    data = request.json
    suggestion = data.get('suggestion')
    if not suggestion:
        return jsonify({'error': 'suggestion required'}), 400

    chats.insert_one({
        'user_id': patient_id,
        'question': None,
        'answer': suggestion,
        'from_role': 'doctor',
        'doctor_id': g.user_id
    })
    return jsonify({'message': 'Suggestion saved'})


@chat_bp.route('/message/<message_id>', methods=['PUT'])
@require_auth
def update_message(message_id):
    data = request.json or {}
    new_question = data.get('question')
    rerun = data.get('rerun', False)

    try:
        doc = chats.find_one({'_id': ObjectId(message_id)})
    except Exception:
        return jsonify({'error': 'invalid id'}), 400
    if not doc:
        return jsonify({'error': 'Not found'}), 404

    # only allow the owning user to edit their message or a doctor to edit their own doctor messages
    if str(doc.get('user_id')) != g.user_id and not (g.role == 'doctor' and doc.get('from_role') == 'doctor' and str(doc.get('doctor_id')) == g.user_id):
        return jsonify({'error': 'Forbidden'}), 403

    update_fields = {}
    if new_question is not None:
        update_fields['question'] = new_question

    # if rerun is requested, regenerate the answer using model
    if rerun:
        role = g.role or 'patient'
        context = doc.get('context', {}) or {}
        answer = generate_answer(new_question or doc.get('question') or '', role=role, context=context)
        update_fields['answer'] = answer
        update_fields['timestamp'] = datetime.utcnow()

    if update_fields:
        chats.update_one({'_id': ObjectId(message_id)}, {'$set': update_fields})

    return jsonify({'message': 'updated'})


@chat_bp.route('/message/<message_id>', methods=['DELETE'])
@require_auth
def delete_message(message_id):
    try:
        doc = chats.find_one({'_id': ObjectId(message_id)})
    except Exception:
        return jsonify({'error': 'invalid id'}), 400
    if not doc:
        return jsonify({'error': 'Not found'}), 404

    # only owner or doctor-owner can delete
    if str(doc.get('user_id')) != g.user_id and not (g.role == 'doctor' and doc.get('from_role') == 'doctor' and str(doc.get('doctor_id')) == g.user_id):
        return jsonify({'error': 'Forbidden'}), 403

    chats.delete_one({'_id': ObjectId(message_id)})
    return jsonify({'message': 'deleted'})


# Medicine Information endpoints
@chat_bp.route('/medicines', methods=['GET'])
def list_medicines():
    """Get list of all available medicines."""
    medicines_list = []
    for med_name, med_info in MEDICINE_DATABASE.items():
        medicines_list.append({
            'name': med_name,
            'category': med_info['category'],
            'uses': med_info['uses'],
            'dosage': med_info['dosage']
        })
    return jsonify({'medicines': medicines_list, 'total': len(medicines_list)})


@chat_bp.route('/medicines/<medicine_name>', methods=['GET'])
def get_medicine_details(medicine_name):
    """Get detailed information about a specific medicine."""
    med_info = _get_medicine_info(medicine_name)
    if not med_info:
        return jsonify({'error': 'Medicine not found'}), 404
    
    med_norm = _normalize_med_name(medicine_name)
    return jsonify({
        'name': med_norm,
        'category': med_info['category'],
        'uses': med_info['uses'],
        'dosage': med_info['dosage'],
        'max_daily': med_info['max_daily'],
        'side_effects': med_info['side_effects'],
        'precautions': med_info['precautions']
    })


@chat_bp.route('/medicines/search', methods=['GET'])
def search_medicines():
    """Search medicines by symptom or use."""
    query = request.args.get('symptom', '').lower()
    if not query:
        return jsonify({'error': 'symptom parameter required'}), 400
    
    results = []
    for med_name, med_info in MEDICINE_DATABASE.items():
        for use in med_info['uses']:
            if query in use.lower():
                results.append({
                    'name': med_name,
                    'category': med_info['category'],
                    'uses': med_info['uses'],
                    'dosage': med_info['dosage']
                })
                break
    
    return jsonify({'results': results, 'count': len(results), 'query': query})
