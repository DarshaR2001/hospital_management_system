'use client';

import { useEffect, useState, useCallback } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { appointmentService } from '@/services/appointmentService';
import { staffService } from '@/services/staffService';
import { patientService } from '@/services/patientService';
import { Appointment, AppointmentCreate, Doctor, Patient } from '@/types';

const STATUSES = ['SCHEDULED', 'CONFIRMED', 'CHECKED_IN', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'NO_SHOW'];

function statusBadge(status: string) {
  const map: Record<string, string> = {
    SCHEDULED: 'badge-scheduled', CONFIRMED: 'badge-confirmed', CHECKED_IN: 'badge-checkedin',
    IN_PROGRESS: 'badge-inprogress', COMPLETED: 'badge-completed',
    CANCELLED: 'badge-cancelled', NO_SHOW: 'badge-noshow',
  };
  return <span className={`badge ${map[status] || 'badge-scheduled'}`}>{status.replace('_', ' ')}</span>;
}

const emptyForm: AppointmentCreate = {
  patient_id: '', doctor_id: '', appointment_date: '', appointment_time: '', reason: '', notes: '',
};

export default function AppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterDate, setFilterDate] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<AppointmentCreate>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [patientSearch, setPatientSearch] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await appointmentService.list({
        appointment_date: filterDate || undefined,
        status: filterStatus || undefined,
        limit: 100,
      });
      setAppointments(data);
    } finally {
      setLoading(false);
    }
  }, [filterDate, filterStatus]);

  useEffect(() => { load(); }, [load]);

  const openModal = async () => {
    setShowModal(true);
    const [docs, pats] = await Promise.all([
      staffService.listDoctors({ is_available: true }),
      patientService.list(undefined, 50),
    ]);
    setDoctors(docs);
    setPatients(pats);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      const created = await appointmentService.create(form);
      setAppointments(prev => [created, ...prev]);
      setShowModal(false);
      setForm(emptyForm);
    } catch (err: unknown) {
      setError(
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Failed to book appointment.'
      );
    } finally {
      setSaving(false);
    }
  };

  const set = (field: keyof AppointmentCreate) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
      setForm(prev => ({ ...prev, [field]: e.target.value }));

  const searchPatients = async () => {
    if (!patientSearch) return;
    const pats = await patientService.list(patientSearch);
    setPatients(pats);
  };

  return (
    <DashboardLayout title="Appointments" subtitle="Schedule and manage appointments">
      <div className="page-header">
        <h1>Appointment Management</h1>
        <p>View, filter and book patient appointments</p>
      </div>

      <div className="card">
        <div className="card-header">
          <div className="flex gap-12" style={{ flex: 1, flexWrap: 'wrap' }}>
            <div className="form-group" style={{ margin: 0 }}>
              <input
                id="filter-date"
                type="date"
                className="form-control"
                value={filterDate}
                onChange={e => setFilterDate(e.target.value)}
                style={{ width: 160 }}
              />
            </div>
            <select
              id="filter-status"
              className="form-control"
              value={filterStatus}
              onChange={e => setFilterStatus(e.target.value)}
              style={{ width: 160 }}
            >
              <option value="">All Statuses</option>
              {STATUSES.map(s => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
            </select>
            <button className="btn btn-secondary" onClick={load}>🔄 Refresh</button>
          </div>
          <button id="book-appointment-btn" className="btn btn-primary" onClick={openModal}>
            ➕ Book Appointment
          </button>
        </div>

        <div className="table-wrap">
          {loading ? (
            <div className="loading-center"><div className="spinner" /><span>Loading appointments...</span></div>
          ) : appointments.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📅</div>
              <p>No appointments found for the selected filters.</p>
            </div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Appt #</th>
                  <th>Patient</th>
                  <th>Doctor</th>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Status</th>
                  <th>Reason</th>
                  <th>Fee</th>
                </tr>
              </thead>
              <tbody>
                {appointments.map(a => (
                  <tr key={a.id}>
                    <td className="td-code">{a.appointment_number}</td>
                    <td>
                      <div className="td-name">{a.patient_name}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{a.patient_phone}</div>
                    </td>
                    <td>
                      <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{a.doctor_name}</div>
                      <div style={{ fontSize: '11px', color: 'var(--accent)' }}>{a.specialization}</div>
                    </td>
                    <td>{a.appointment_date}</td>
                    <td>{a.appointment_time}</td>
                    <td>{statusBadge(a.status)}</td>
                    <td style={{ maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {a.reason || '—'}
                    </td>
                    <td>₹{a.consultation_fee?.toFixed(0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Book Appointment Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Book Appointment</h3>
              <button className="modal-close" onClick={() => setShowModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreate}>
              <div className="modal-body">
                {error && <div className="login-error">{error}</div>}

                <div className="form-group">
                  <label className="form-label">Patient *</label>
                  <div style={{ display: 'flex', gap: '8px', marginBottom: '6px' }}>
                    <input
                      className="form-control"
                      placeholder="Search patient..."
                      value={patientSearch}
                      onChange={e => setPatientSearch(e.target.value)}
                    />
                    <button type="button" className="btn btn-secondary btn-sm" onClick={searchPatients}>Search</button>
                  </div>
                  <select
                    id="appt-patient"
                    className="form-control"
                    value={form.patient_id}
                    onChange={set('patient_id')}
                    required
                  >
                    <option value="">— Select Patient —</option>
                    {patients.map(p => (
                      <option key={p.id} value={p.id}>
                        {p.first_name} {p.last_name} ({p.patient_code})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Doctor *</label>
                  <select
                    id="appt-doctor"
                    className="form-control"
                    value={form.doctor_id}
                    onChange={set('doctor_id')}
                    required
                  >
                    <option value="">— Select Doctor —</option>
                    {doctors.map(d => (
                      <option key={d.id} value={d.id}>
                        Dr. {d.employee?.user?.full_name} – {d.specialization}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-row form-row-2">
                  <div className="form-group">
                    <label className="form-label">Date *</label>
                    <input id="appt-date" type="date" className="form-control" value={form.appointment_date} onChange={set('appointment_date')} required />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Time *</label>
                    <input id="appt-time" type="time" className="form-control" value={form.appointment_time} onChange={set('appointment_time')} required />
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Reason for Visit</label>
                  <input id="appt-reason" className="form-control" value={form.reason} onChange={set('reason')} placeholder="e.g. Regular check-up" />
                </div>

                <div className="form-group">
                  <label className="form-label">Notes</label>
                  <textarea id="appt-notes" className="form-control" rows={2} value={form.notes} onChange={set('notes')} />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button id="save-appointment-btn" type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? <><span className="spinner" style={{ width: 14, height: 14 }} /> Booking...</> : '📅 Book Appointment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
