'use client';

import { useEffect, useState, useCallback } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { patientService } from '@/services/patientService';
import { Patient, PatientCreate } from '@/types';

const GENDERS = ['MALE', 'FEMALE', 'OTHER'];
const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

const emptyForm: PatientCreate = {
  first_name: '', last_name: '', gender: 'MALE', dob: '',
  phone: '', blood_group: '', email: '', address: '',
  emergency_contact: '', emergency_phone: '',
};

export default function PatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<PatientCreate>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async (q?: string) => {
    setLoading(true);
    try {
      const data = await patientService.list(q || undefined);
      setPatients(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    load(search);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      const created = await patientService.create(form);
      setPatients(prev => [created, ...prev]);
      setShowModal(false);
      setForm(emptyForm);
    } catch (err: unknown) {
      setError(
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Failed to register patient.'
      );
    } finally {
      setSaving(false);
    }
  };

  const set = (field: keyof PatientCreate) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm(prev => ({ ...prev, [field]: e.target.value }));

  const genderBadge = (g: string) => {
    const cls = g === 'MALE' ? 'badge-male' : g === 'FEMALE' ? 'badge-female' : 'badge-other';
    return <span className={`badge ${cls}`}>{g}</span>;
  };

  return (
    <DashboardLayout title="Patients" subtitle="Manage patient records">
      <div className="page-header">
        <h1>Patient Registry</h1>
        <p>Search, register and manage all patients</p>
      </div>

      <div className="card">
        <div className="card-header">
          <div className="toolbar" style={{ margin: 0, flex: 1 }}>
            <form onSubmit={handleSearch} className="search-bar">
              <span className="search-icon">🔍</span>
              <input
                id="patient-search"
                type="text"
                placeholder="Search name, phone, code..."
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
            </form>
            <button id="patient-search-btn" className="btn btn-secondary" onClick={() => load(search)}>
              Search
            </button>
          </div>
          <button id="register-patient-btn" className="btn btn-primary" onClick={() => setShowModal(true)}>
            ➕ Register Patient
          </button>
        </div>

        <div className="table-wrap">
          {loading ? (
            <div className="loading-center"><div className="spinner" /><span>Loading patients...</span></div>
          ) : patients.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">👥</div>
              <p>No patients found. Register the first patient!</p>
            </div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Name</th>
                  <th>Gender</th>
                  <th>DOB</th>
                  <th>Blood Group</th>
                  <th>Phone</th>
                  <th>Registered</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {patients.map(p => (
                  <tr key={p.id}>
                    <td className="td-code">{p.patient_code}</td>
                    <td className="td-name">{p.first_name} {p.last_name}</td>
                    <td>{genderBadge(p.gender)}</td>
                    <td>{p.dob}</td>
                    <td>{p.blood_group || '—'}</td>
                    <td>{p.phone}</td>
                    <td>{new Date(p.created_at).toLocaleDateString()}</td>
                    <td>
                      <a href={`/patients/${p.id}`} className="btn btn-secondary btn-sm">
                        View
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Register Patient Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal modal-lg" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Register New Patient</h3>
              <button className="modal-close" onClick={() => setShowModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreate}>
              <div className="modal-body">
                {error && <div className="login-error">{error}</div>}
                <div className="form-row form-row-2">
                  <div className="form-group">
                    <label className="form-label">First Name *</label>
                    <input id="p-first-name" className="form-control" value={form.first_name} onChange={set('first_name')} required />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Last Name *</label>
                    <input id="p-last-name" className="form-control" value={form.last_name} onChange={set('last_name')} required />
                  </div>
                </div>
                <div className="form-row form-row-3">
                  <div className="form-group">
                    <label className="form-label">Gender *</label>
                    <select id="p-gender" className="form-control" value={form.gender} onChange={set('gender')} required>
                      {GENDERS.map(g => <option key={g}>{g}</option>)}
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Date of Birth *</label>
                    <input id="p-dob" type="date" className="form-control" value={form.dob} onChange={set('dob')} required />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Blood Group</label>
                    <select id="p-blood-group" className="form-control" value={form.blood_group} onChange={set('blood_group')}>
                      <option value="">— Select —</option>
                      {BLOOD_GROUPS.map(b => <option key={b}>{b}</option>)}
                    </select>
                  </div>
                </div>
                <div className="form-row form-row-2">
                  <div className="form-group">
                    <label className="form-label">Phone *</label>
                    <input id="p-phone" className="form-control" value={form.phone} onChange={set('phone')} required />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Email</label>
                    <input id="p-email" type="email" className="form-control" value={form.email} onChange={set('email')} />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Address</label>
                  <textarea id="p-address" className="form-control" rows={2} value={form.address} onChange={set('address')} />
                </div>
                <div className="form-row form-row-2">
                  <div className="form-group">
                    <label className="form-label">Emergency Contact</label>
                    <input id="p-emergency-contact" className="form-control" value={form.emergency_contact} onChange={set('emergency_contact')} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Emergency Phone</label>
                    <input id="p-emergency-phone" className="form-control" value={form.emergency_phone} onChange={set('emergency_phone')} />
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button id="save-patient-btn" type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? <><span className="spinner" style={{ width: 14, height: 14 }} /> Saving...</> : '💾 Register Patient'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
