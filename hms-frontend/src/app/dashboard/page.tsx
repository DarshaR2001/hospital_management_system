'use client';

import { useEffect, useState } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import api from '@/lib/api';

interface DashboardStats {
  patients: { total: number };
  appointments: { today_total: number; today_completed: number };
  inpatient: { active_admissions: number; total_beds: number; available_beds: number; occupied_beds: number };
  laboratory: { pending_tests: number };
  pharmacy: { low_stock_medicines: number; total_medicines: number };
  financials: { total_billed: number; total_collected: number; total_outstanding: number };
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<DashboardStats>('/reports/dashboard-stats')
      .then(r => setStats(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const fmt = (n: number) =>
    new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n);

  return (
    <DashboardLayout title="Dashboard" subtitle="Overview of hospital operations">
      <div className="page-header">
        <h1>Hospital Overview</h1>
        <p>Real-time snapshot of today&apos;s hospital activity</p>
      </div>

      {loading ? (
        <div className="loading-center"><div className="spinner" /><span>Loading stats...</span></div>
      ) : stats ? (
        <>
          {/* Stats Grid */}
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon teal">👥</div>
              <div className="stat-info">
                <h3>{stats.patients.total}</h3>
                <p>Total Patients</p>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon blue">📅</div>
              <div className="stat-info">
                <h3>{stats.appointments.today_total}</h3>
                <p>Appointments Today</p>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon green">✅</div>
              <div className="stat-info">
                <h3>{stats.appointments.today_completed}</h3>
                <p>Completed Today</p>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon yellow">🛏️</div>
              <div className="stat-info">
                <h3>{stats.inpatient.active_admissions}</h3>
                <p>Active Admissions</p>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon purple">🧪</div>
              <div className="stat-info">
                <h3>{stats.laboratory.pending_tests}</h3>
                <p>Pending Lab Tests</p>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon red">💊</div>
              <div className="stat-info">
                <h3>{stats.pharmacy.low_stock_medicines}</h3>
                <p>Low Stock Medicines</p>
              </div>
            </div>
          </div>

          {/* Financial + Bed Summary */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            {/* Financials */}
            <div className="card">
              <div className="card-header">
                <span className="card-title">💳 Financial Summary</span>
              </div>
              <div className="card-body">
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <FinRow label="Total Billed" value={fmt(stats.financials.total_billed)} color="var(--text-primary)" />
                  <FinRow label="Total Collected" value={fmt(stats.financials.total_collected)} color="var(--success)" />
                  <FinRow label="Outstanding" value={fmt(stats.financials.total_outstanding)} color="var(--warning)" />
                </div>
              </div>
            </div>

            {/* Bed Occupancy */}
            <div className="card">
              <div className="card-header">
                <span className="card-title">🛏️ Bed Occupancy</span>
              </div>
              <div className="card-body">
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <FinRow label="Total Beds" value={String(stats.inpatient.total_beds)} color="var(--text-primary)" />
                  <FinRow label="Occupied" value={String(stats.inpatient.occupied_beds)} color="var(--danger)" />
                  <FinRow label="Available" value={String(stats.inpatient.available_beds)} color="var(--success)" />
                </div>

                {stats.inpatient.total_beds > 0 && (
                  <div style={{ marginTop: '20px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '12px', color: 'var(--text-muted)' }}>
                      <span>Occupancy Rate</span>
                      <span>{Math.round((stats.inpatient.occupied_beds / stats.inpatient.total_beds) * 100)}%</span>
                    </div>
                    <div style={{ height: '8px', background: 'var(--bg-input)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div style={{
                        height: '100%',
                        background: 'linear-gradient(90deg, var(--accent), var(--blue))',
                        width: `${Math.round((stats.inpatient.occupied_beds / stats.inpatient.total_beds) * 100)}%`,
                        borderRadius: '4px',
                        transition: 'width 0.5s ease',
                      }} />
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Quick Links */}
          <div className="card" style={{ marginTop: '20px' }}>
            <div className="card-header">
              <span className="card-title">⚡ Quick Actions</span>
            </div>
            <div className="card-body">
              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                {[
                  { href: '/patients', label: '➕ Register Patient', color: 'var(--accent)' },
                  { href: '/appointments', label: '📅 Book Appointment', color: 'var(--blue)' },
                  { href: '/laboratory', label: '🧪 Lab Requests', color: '#a855f7' },
                  { href: '/billing', label: '💳 Create Invoice', color: 'var(--warning)' },
                  { href: '/inpatient', label: '🛏️ Admit Patient', color: 'var(--success)' },
                ].map((link) => (
                  <a
                    key={link.href}
                    href={link.href}
                    className="btn btn-secondary"
                    style={{ borderColor: link.color, color: link.color }}
                  >
                    {link.label}
                  </a>
                ))}
              </div>
            </div>
          </div>
        </>
      ) : (
        <div className="empty-state">
          <div className="empty-icon">⚠️</div>
          <p>Could not load dashboard stats. Make sure the backend is running.</p>
        </div>
      )}
    </DashboardLayout>
  );
}

function FinRow({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{label}</span>
      <span style={{ fontSize: '15px', fontWeight: 700, color }}>{value}</span>
    </div>
  );
}
