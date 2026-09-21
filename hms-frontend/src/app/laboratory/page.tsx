'use client';

import { useEffect, useState } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import api from '@/lib/api';

interface LabTestRequest {
  id: string;
  request_number: string;
  patient_id: string;
  doctor_id: string;
  status: string;
  priority: string;
  clinical_notes?: string;
  patient_name?: string;
  patient_code?: string;
  doctor_name?: string;
  results: LabResult[];
  created_at: string;
}

interface LabResult {
  id: string;
  test_name?: string;
  test_code?: string;
  result_value?: string;
  normal_range?: string;
  units?: string;
  status: string;
  remarks?: string;
  created_at: string;
}

function statusBadge(s: string) {
  const map: Record<string, string> = {
    REQUESTED: 'badge-scheduled',
    SAMPLE_COLLECTED: 'badge-checkedin',
    IN_PROGRESS: 'badge-inprogress',
    COMPLETED: 'badge-completed',
    CANCELLED: 'badge-cancelled',
  };
  return <span className={`badge ${map[s] || 'badge-scheduled'}`}>{s.replace('_', ' ')}</span>;
}

function priorityBadge(p: string) {
  const map: Record<string, string> = { ROUTINE: 'badge-scheduled', URGENT: 'badge-pending', STAT: 'badge-noshow' };
  return <span className={`badge ${map[p] || 'badge-scheduled'}`}>{p}</span>;
}

export default function LaboratoryPage() {
  const [requests, setRequests] = useState<LabTestRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<LabTestRequest | null>(null);
  const [filterStatus, setFilterStatus] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = { limit: '100' };
      if (filterStatus) params.status = filterStatus;
      const res = await api.get<LabTestRequest[]>('/lab/requests', { params });
      setRequests(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [filterStatus]); // eslint-disable-line react-hooks/exhaustive-deps

  const STATUSES = ['REQUESTED', 'SAMPLE_COLLECTED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'];

  return (
    <DashboardLayout title="Laboratory" subtitle="Manage lab test requests and results">
      <div className="page-header">
        <h1>Laboratory Management</h1>
        <p>Track test requests, sample collection, and results</p>
      </div>

      <div className="card">
        <div className="card-header">
          <div className="flex gap-12">
            <select
              id="lab-filter-status"
              className="form-control"
              value={filterStatus}
              onChange={e => setFilterStatus(e.target.value)}
              style={{ width: 180 }}
            >
              <option value="">All Statuses</option>
              {STATUSES.map(s => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
            </select>
            <button className="btn btn-secondary" onClick={load}>🔄 Refresh</button>
          </div>
        </div>

        <div className="table-wrap">
          {loading ? (
            <div className="loading-center"><div className="spinner" /><span>Loading lab requests...</span></div>
          ) : requests.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">🧪</div>
              <p>No lab requests found for the selected filter.</p>
            </div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Request #</th>
                  <th>Patient</th>
                  <th>Doctor</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Tests</th>
                  <th>Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {requests.map(r => (
                  <tr key={r.id}>
                    <td className="td-code">{r.request_number}</td>
                    <td>
                      <div className="td-name">{r.patient_name}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{r.patient_code}</div>
                    </td>
                    <td>{r.doctor_name}</td>
                    <td>{priorityBadge(r.priority)}</td>
                    <td>{statusBadge(r.status)}</td>
                    <td>{r.results.length} test(s)</td>
                    <td>{new Date(r.created_at).toLocaleDateString()}</td>
                    <td>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => setSelected(r)}
                      >
                        View Results
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Results Modal */}
      {selected && (
        <div className="modal-overlay" onClick={() => setSelected(null)}>
          <div className="modal modal-lg" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Lab Results – {selected.request_number}</h3>
              <button className="modal-close" onClick={() => setSelected(null)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="detail-grid" style={{ marginBottom: '16px' }}>
                <div className="detail-item"><label>Patient</label><span>{selected.patient_name}</span></div>
                <div className="detail-item"><label>Doctor</label><span>{selected.doctor_name}</span></div>
                <div className="detail-item"><label>Status</label><span>{statusBadge(selected.status)}</span></div>
                <div className="detail-item"><label>Priority</label><span>{priorityBadge(selected.priority)}</span></div>
              </div>
              {selected.results.length === 0 ? (
                <div className="empty-state" style={{ padding: '30px' }}>
                  <p>No results recorded yet.</p>
                </div>
              ) : (
                <table>
                  <thead>
                    <tr>
                      <th>Test</th>
                      <th>Code</th>
                      <th>Result</th>
                      <th>Normal Range</th>
                      <th>Units</th>
                      <th>Status</th>
                      <th>Remarks</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selected.results.map(r => (
                      <tr key={r.id}>
                        <td className="td-name">{r.test_name}</td>
                        <td className="td-code">{r.test_code}</td>
                        <td style={{ fontWeight: 600 }}>{r.result_value || '—'}</td>
                        <td>{r.normal_range || '—'}</td>
                        <td>{r.units || '—'}</td>
                        <td>{statusBadge(r.status)}</td>
                        <td>{r.remarks || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
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
