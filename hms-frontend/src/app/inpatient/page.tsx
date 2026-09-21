'use client';

import { useEffect, useState } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import api from '@/lib/api';

interface Admission {
  id: string;
  admission_number: string;
  patient_id: string;
  doctor_id: string;
  bed_id?: string;
  admission_date: string;
  discharge_date?: string;
  admission_reason: string;
  discharge_summary?: string;
  status: string;
  patient_name?: string;
  patient_code?: string;
  doctor_name?: string;
  bed_number?: string;
  ward_name?: string;
  created_at: string;
}

interface Ward {
  id: string;
  name: string;
  ward_type: string;
  total_beds: number;
  available_beds: number;
  occupied_beds: number;
  is_active: boolean;
}

function statusBadge(s: string) {
  const map: Record<string, string> = {
    ADMITTED: 'badge-admitted',
    DISCHARGED: 'badge-discharged',
    TRANSFERRED: 'badge-inprogress',
  };
  return <span className={`badge ${map[s] || 'badge-scheduled'}`}>{s}</span>;
}

export default function InpatientPage() {
  const [admissions, setAdmissions] = useState<Admission[]>([]);
  const [wards, setWards] = useState<Ward[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('ADMITTED');
  const [selected, setSelected] = useState<Admission | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = { limit: '100' };
      if (filterStatus) params.status = filterStatus;
      const [admRes, wardRes] = await Promise.all([
        api.get<Admission[]>('/inpatient/admissions', { params }),
        api.get<Ward[]>('/inpatient/wards'),
      ]);
      setAdmissions(admRes.data);
      setWards(wardRes.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [filterStatus]); // eslint-disable-line react-hooks/exhaustive-deps

  const totalBeds = wards.reduce((s, w) => s + w.total_beds, 0);
  const availableBeds = wards.reduce((s, w) => s + w.available_beds, 0);

  return (
    <DashboardLayout title="Inpatient" subtitle="Ward management and patient admissions">
      <div className="page-header">
        <h1>Inpatient Management</h1>
        <p>Manage ward occupancy, admissions and discharges</p>
      </div>

      {/* Ward Summary */}
      {wards.length > 0 && (
        <div className="card" style={{ marginBottom: '20px' }}>
          <div className="card-header">
            <span className="card-title">🏥 Ward Summary</span>
            <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
              {availableBeds}/{totalBeds} beds available
            </div>
          </div>
          <div className="card-body">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '14px' }}>
              {wards.map(w => (
                <div key={w.id} style={{
                  background: 'var(--bg-input)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius)',
                  padding: '14px 16px',
                }}>
                  <div style={{ fontWeight: 600, marginBottom: '4px' }}>{w.name}</div>
                  <div style={{ fontSize: '11px', color: 'var(--accent)', marginBottom: '10px', textTransform: 'uppercase' }}>
                    {w.ward_type}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-secondary)' }}>
                    <span>Available</span>
                    <span style={{ color: w.available_beds === 0 ? 'var(--danger)' : 'var(--success)', fontWeight: 600 }}>
                      {w.available_beds}/{w.total_beds}
                    </span>
                  </div>
                  <div style={{ marginTop: '8px', height: '5px', background: 'var(--border)', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{
                      height: '100%',
                      background: w.available_beds === 0 ? 'var(--danger)' : 'var(--accent)',
                      width: `${Math.round(((w.total_beds - w.available_beds) / w.total_beds) * 100)}%`,
                    }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Admissions Table */}
      <div className="card">
        <div className="card-header">
          <div className="flex gap-12">
            <select
              id="inpatient-filter-status"
              className="form-control"
              value={filterStatus}
              onChange={e => setFilterStatus(e.target.value)}
              style={{ width: 160 }}
            >
              <option value="">All Statuses</option>
              {['ADMITTED', 'DISCHARGED', 'TRANSFERRED'].map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <button className="btn btn-secondary" onClick={load}>🔄 Refresh</button>
          </div>
        </div>

        <div className="table-wrap">
          {loading ? (
            <div className="loading-center"><div className="spinner" /><span>Loading admissions...</span></div>
          ) : admissions.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">🛏️</div>
              <p>No admissions found for the selected filter.</p>
            </div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Admission #</th>
                  <th>Patient</th>
                  <th>Doctor</th>
                  <th>Ward / Bed</th>
                  <th>Admitted On</th>
                  <th>Discharged</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {admissions.map(a => (
                  <tr key={a.id}>
                    <td className="td-code">{a.admission_number}</td>
                    <td>
                      <div className="td-name">{a.patient_name}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{a.patient_code}</div>
                    </td>
                    <td>{a.doctor_name}</td>
                    <td>
                      <div style={{ fontWeight: 500 }}>{a.ward_name || '—'}</div>
                      <div style={{ fontSize: '11px', color: 'var(--accent)' }}>Bed: {a.bed_number || '—'}</div>
                    </td>
                    <td>{a.admission_date}</td>
                    <td>{a.discharge_date || '—'}</td>
                    <td>{statusBadge(a.status)}</td>
                    <td>
                      <button className="btn btn-secondary btn-sm" onClick={() => setSelected(a)}>
                        Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Admission Detail Modal */}
      {selected && (
        <div className="modal-overlay" onClick={() => setSelected(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Admission – {selected.admission_number}</h3>
              <button className="modal-close" onClick={() => setSelected(null)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="detail-grid">
                <div className="detail-item"><label>Patient</label><span>{selected.patient_name}</span></div>
                <div className="detail-item"><label>Patient Code</label><span>{selected.patient_code}</span></div>
                <div className="detail-item"><label>Doctor</label><span>{selected.doctor_name}</span></div>
                <div className="detail-item"><label>Status</label><span>{statusBadge(selected.status)}</span></div>
                <div className="detail-item"><label>Ward</label><span>{selected.ward_name || '—'}</span></div>
                <div className="detail-item"><label>Bed</label><span>{selected.bed_number || '—'}</span></div>
                <div className="detail-item"><label>Admitted On</label><span>{selected.admission_date}</span></div>
                <div className="detail-item"><label>Discharged On</label><span>{selected.discharge_date || 'Not discharged'}</span></div>
              </div>
              <div className="form-group" style={{ marginTop: '16px' }}>
                <label className="form-label">Admission Reason</label>
                <div style={{ background: 'var(--bg-input)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', fontSize: '14px' }}>
                  {selected.admission_reason}
                </div>
              </div>
              {selected.discharge_summary && (
                <div className="form-group">
                  <label className="form-label">Discharge Summary</label>
                  <div style={{ background: 'var(--bg-input)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', fontSize: '14px' }}>
                    {selected.discharge_summary}
                  </div>
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
