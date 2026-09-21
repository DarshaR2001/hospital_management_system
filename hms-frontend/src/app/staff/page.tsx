'use client';

import { useEffect, useState } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import api from '@/lib/api';

interface EmployeeResponse {
  id: string;
  employee_code: string;
  designation: string;
  qualification?: string;
  joining_date: string;
  department_id?: string;
  full_name?: string;
  email?: string;
  phone?: string;
  department_name?: string;
  created_at: string;
}

interface DoctorResponse {
  id: string;
  specialization: string;
  license_number: string;
  consultation_fee: number;
  room_number?: string;
  employee_id: string;
  doctor_name?: string;
  department_name?: string;
  email?: string;
  phone?: string;
  created_at: string;
}

interface Department {
  id: string;
  name: string;
  code: string;
  description?: string;
}

export default function StaffPage() {
  const [tab, setTab] = useState<'employees' | 'doctors'>('employees');
  const [employees, setEmployees] = useState<EmployeeResponse[]>([]);
  const [doctors, setDoctors] = useState<DoctorResponse[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      try {
        const [empRes, docRes, deptRes] = await Promise.all([
          api.get<EmployeeResponse[]>('/employees'),
          api.get<DoctorResponse[]>('/doctors'),
          api.get<Department[]>('/departments'),
        ]);
        setEmployees(empRes.data);
        setDoctors(docRes.data);
        setDepartments(deptRes.data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  return (
    <DashboardLayout title="Staff" subtitle="Manage employees and doctors">
      <div className="page-header">
        <h1>Staff Management</h1>
        <p>View all hospital employees and doctors</p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '4px', marginBottom: '20px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius)', padding: '4px', width: 'fit-content' }}>
        <button
          id="tab-employees"
          className={`btn ${tab === 'employees' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ borderRadius: 'var(--radius-sm)' }}
          onClick={() => setTab('employees')}
        >
          👨‍💼 Employees ({employees.length})
        </button>
        <button
          id="tab-doctors"
          className={`btn ${tab === 'doctors' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ borderRadius: 'var(--radius-sm)' }}
          onClick={() => setTab('doctors')}
        >
          👨‍⚕️ Doctors ({doctors.length})
        </button>
      </div>

      {/* Departments Summary */}
      {departments.length > 0 && (
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '20px' }}>
          {departments.map(d => (
            <span key={d.id} className="badge badge-active" style={{ fontSize: '12px', padding: '4px 12px' }}>
              🏢 {d.name}
            </span>
          ))}
        </div>
      )}

      <div className="card">
        <div className="table-wrap">
          {loading ? (
            <div className="loading-center"><div className="spinner" /><span>Loading staff...</span></div>
          ) : tab === 'employees' ? (
            employees.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">👨‍💼</div>
                <p>No employees found. Use POST /api/v1/auth/seed to add seed data.</p>
              </div>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Emp Code</th>
                    <th>Name</th>
                    <th>Designation</th>
                    <th>Department</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>Joined</th>
                  </tr>
                </thead>
                <tbody>
                  {employees.map(e => (
                    <tr key={e.id}>
                      <td className="td-code">{e.employee_code}</td>
                      <td className="td-name">{e.full_name}</td>
                      <td>{e.designation}</td>
                      <td>{e.department_name || '—'}</td>
                      <td style={{ fontSize: '12px' }}>{e.email}</td>
                      <td>{e.phone || '—'}</td>
                      <td>{e.joining_date}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )
          ) : (
            doctors.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">👨‍⚕️</div>
                <p>No doctors found. Add doctors via the API.</p>
              </div>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Specialization</th>
                    <th>Department</th>
                    <th>License No.</th>
                    <th>Room</th>
                    <th>Consult Fee</th>
                    <th>Email</th>
                  </tr>
                </thead>
                <tbody>
                  {doctors.map(d => (
                    <tr key={d.id}>
                      <td className="td-name">Dr. {d.doctor_name}</td>
                      <td><span className="badge badge-active">{d.specialization}</span></td>
                      <td>{d.department_name || '—'}</td>
                      <td className="td-code">{d.license_number}</td>
                      <td>{d.room_number || '—'}</td>
                      <td style={{ color: 'var(--success)', fontWeight: 600 }}>₹{d.consultation_fee}</td>
                      <td style={{ fontSize: '12px' }}>{d.email}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
