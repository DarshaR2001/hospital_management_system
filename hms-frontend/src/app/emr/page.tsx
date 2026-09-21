'use client';

import { useEffect, useState } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import api from '@/lib/api';

interface MedicalRecord {
  id: string;
  record_number: string;
  patient_id: string;
  doctor_id: string;
  visit_date: string;
  chief_complaint: string;
  diagnoses: Diagnosis[];
  treatments: Treatment[];
  prescriptions: Prescription[];
  vital_signs?: Record<string, string>;
  patient_name?: string;
  patient_code?: string;
  doctor_name?: string;
  created_at: string;
}

interface Diagnosis {
  id: string;
  icd_code?: string;
  description: string;
  diagnosis_type: string;
}

interface Treatment {
  id: string;
  description: string;
  procedure_code?: string;
}

interface Prescription {
  id: string;
  prescription_code: string;
  status: string;
  items: PrescriptionItem[];
}

interface PrescriptionItem {
  id: string;
  medicine_name?: string;
  dosage: string;
  frequency: string;
  duration: string;
  instructions?: string;
  quantity: number;
}

export default function EMRPage() {
  const [records, setRecords] = useState<MedicalRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<MedicalRecord | null>(null);
  const [search, setSearch] = useState('');

  const load = async (q?: string) => {
    setLoading(true);
    try {
      const params: Record<string, string> = { limit: '100' };
      if (q) params.patient_code = q;
      const res = await api.get<MedicalRecord[]>('/emr/records', { params });
      setRecords(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <DashboardLayout title="Medical Records" subtitle="Electronic medical records and prescriptions">
      <div className="page-header">
        <h1>Electronic Medical Records</h1>
        <p>View patient consultations, diagnoses, treatments and prescriptions</p>
      </div>

      <div className="card">
        <div className="card-header">
          <form
            className="search-bar"
            onSubmit={e => { e.preventDefault(); load(search); }}
          >
            <span className="search-icon">🔍</span>
            <input
              id="emr-search"
              type="text"
              placeholder="Search by patient code..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </form>
          <button className="btn btn-secondary" onClick={() => load(search)}>Search</button>
        </div>

        <div className="table-wrap">
          {loading ? (
            <div className="loading-center"><div className="spinner" /><span>Loading records...</span></div>
          ) : records.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📋</div>
              <p>No medical records found.</p>
            </div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Record #</th>
                  <th>Patient</th>
                  <th>Doctor</th>
                  <th>Visit Date</th>
                  <th>Chief Complaint</th>
                  <th>Diagnoses</th>
                  <th>Prescriptions</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {records.map(r => (
                  <tr key={r.id}>
                    <td className="td-code">{r.record_number}</td>
                    <td>
                      <div className="td-name">{r.patient_name}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{r.patient_code}</div>
                    </td>
                    <td>{r.doctor_name}</td>
                    <td>{r.visit_date}</td>
                    <td style={{ maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {r.chief_complaint}
                    </td>
                    <td>{r.diagnoses?.length ?? 0}</td>
                    <td>{r.prescriptions?.length ?? 0}</td>
                    <td>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => setSelected(r)}
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* EMR Detail Modal */}
      {selected && (
        <div className="modal-overlay" onClick={() => setSelected(null)}>
          <div className="modal modal-lg" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Medical Record – {selected.record_number}</h3>
              <button className="modal-close" onClick={() => setSelected(null)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="detail-grid" style={{ marginBottom: '16px' }}>
                <div className="detail-item"><label>Patient</label><span>{selected.patient_name}</span></div>
                <div className="detail-item"><label>Patient Code</label><span>{selected.patient_code}</span></div>
                <div className="detail-item"><label>Doctor</label><span>{selected.doctor_name}</span></div>
                <div className="detail-item"><label>Visit Date</label><span>{selected.visit_date}</span></div>
              </div>

              <div className="form-group">
                <label className="form-label">Chief Complaint</label>
                <div style={{ background: 'var(--bg-input)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', fontSize: '14px' }}>
                  {selected.chief_complaint}
                </div>
              </div>

              {selected.vital_signs && Object.keys(selected.vital_signs).length > 0 && (
                <div className="form-group">
                  <label className="form-label">Vital Signs</label>
                  <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                    {Object.entries(selected.vital_signs).map(([k, v]) => (
                      <div key={k} style={{ background: 'var(--bg-input)', padding: '8px 14px', borderRadius: 'var(--radius-sm)', fontSize: '13px' }}>
                        <span style={{ color: 'var(--text-muted)', marginRight: '6px' }}>{k}:</span>
                        <span style={{ fontWeight: 600 }}>{v}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selected.diagnoses?.length > 0 && (
                <div className="form-group">
                  <label className="form-label">Diagnoses</label>
                  {selected.diagnoses.map(d => (
                    <div key={d.id} style={{ background: 'var(--bg-input)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', marginBottom: '6px', fontSize: '13px' }}>
                      <span className="badge badge-inprogress" style={{ marginRight: '8px' }}>{d.diagnosis_type}</span>
                      {d.icd_code && <span className="td-code" style={{ marginRight: '8px' }}>{d.icd_code}</span>}
                      {d.description}
                    </div>
                  ))}
                </div>
              )}

              {selected.treatments?.length > 0 && (
                <div className="form-group">
                  <label className="form-label">Treatments</label>
                  {selected.treatments.map(t => (
                    <div key={t.id} style={{ background: 'var(--bg-input)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', marginBottom: '6px', fontSize: '13px' }}>
                      {t.procedure_code && <span className="td-code" style={{ marginRight: '8px' }}>{t.procedure_code}</span>}
                      {t.description}
                    </div>
                  ))}
                </div>
              )}

              {selected.prescriptions?.length > 0 && (
                <div className="form-group">
                  <label className="form-label">Prescriptions</label>
                  {selected.prescriptions.map(rx => (
                    <div key={rx.id} style={{ background: 'var(--bg-input)', borderRadius: 'var(--radius-sm)', marginBottom: '8px', overflow: 'hidden' }}>
                      <div style={{ padding: '8px 14px', borderBottom: '1px solid var(--border)', display: 'flex', gap: '10px', alignItems: 'center' }}>
                        <span className="td-code">{rx.prescription_code}</span>
                        <span className={`badge ${rx.status === 'DISPENSED' ? 'badge-completed' : 'badge-pending'}`}>{rx.status}</span>
                      </div>
                      <table style={{ margin: 0 }}>
                        <thead>
                          <tr>
                            <th>Medicine</th><th>Dosage</th><th>Frequency</th><th>Duration</th><th>Qty</th>
                          </tr>
                        </thead>
                        <tbody>
                          {rx.items.map(it => (
                            <tr key={it.id}>
                              <td className="td-name">{it.medicine_name}</td>
                              <td>{it.dosage}</td>
                              <td>{it.frequency}</td>
                              <td>{it.duration}</td>
                              <td>{it.quantity}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setSelected(null)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
