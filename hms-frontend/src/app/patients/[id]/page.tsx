'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { patientService } from '@/services/patientService';
import { PatientHistory } from '@/types';

export default function PatientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [patient, setPatient] = useState<PatientHistory | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    patientService.history(id)
      .then(setPatient)
      .catch(() => router.replace('/patients'))
      .finally(() => setLoading(false));
  }, [id, router]);

  if (loading) return (
    <DashboardLayout title="Patient Detail">
      <div className="loading-center"><div className="spinner" /><span>Loading...</span></div>
    </DashboardLayout>
  );

  if (!patient) return null;

  return (
    <DashboardLayout title="Patient Detail" subtitle={patient.patient_code}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
        <button className="btn btn-secondary" onClick={() => router.back()}>← Back</button>
        <div>
          <h1 style={{ fontSize: '22px', fontWeight: 700 }}>
            {patient.first_name} {patient.last_name}
          </h1>
          <span className="td-code">{patient.patient_code}</span>
        </div>
      </div>

      {/* Personal Info */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <div className="card-header"><span className="card-title">👤 Personal Information</span></div>
        <div className="card-body">
          <div className="detail-grid">
            <div className="detail-item"><label>Full Name</label><span>{patient.first_name} {patient.last_name}</span></div>
            <div className="detail-item"><label>Gender</label><span>{patient.gender}</span></div>
            <div className="detail-item"><label>Date of Birth</label><span>{patient.dob}</span></div>
            <div className="detail-item"><label>Blood Group</label><span>{patient.blood_group || '—'}</span></div>
            <div className="detail-item"><label>Phone</label><span>{patient.phone}</span></div>
            <div className="detail-item"><label>Email</label><span>{patient.email || '—'}</span></div>
            <div className="detail-item"><label>Address</label><span>{patient.address || '—'}</span></div>
            <div className="detail-item"><label>Registered</label><span>{new Date(patient.created_at).toLocaleDateString()}</span></div>
          </div>
        </div>
      </div>

      {/* Emergency Contact */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <div className="card-header"><span className="card-title">🆘 Emergency Contact</span></div>
        <div className="card-body">
          <div className="detail-grid">
            <div className="detail-item"><label>Contact Name</label><span>{patient.emergency_contact || '—'}</span></div>
            <div className="detail-item"><label>Contact Phone</label><span>{patient.emergency_phone || '—'}</span></div>
          </div>
        </div>
      </div>

      {/* Medical History Summary */}
      <div className="card">
        <div className="card-header"><span className="card-title">📊 Medical History Summary</span></div>
        <div className="card-body">
          <div className="stats-grid">
            {[
              { icon: '📅', label: 'Appointments', value: patient.appointments_count, color: 'blue' },
              { icon: '📋', label: 'Medical Records', value: patient.medical_records_count, color: 'teal' },
              { icon: '💊', label: 'Prescriptions', value: patient.prescriptions_count, color: 'purple' },
              { icon: '🧪', label: 'Lab Requests', value: patient.lab_requests_count, color: 'yellow' },
              { icon: '💳', label: 'Invoices', value: patient.invoices_count, color: 'green' },
              { icon: '🛏️', label: 'Admissions', value: patient.admissions_count, color: 'red' },
            ].map(item => (
              <div className="stat-card" key={item.label}>
                <div className={`stat-icon ${item.color}`}>{item.icon}</div>
                <div className="stat-info">
                  <h3>{item.value}</h3>
                  <p>{item.label}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
