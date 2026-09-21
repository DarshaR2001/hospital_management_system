'use client';

import { useEffect, useState } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import api from '@/lib/api';

interface InvoiceItem {
  id: string;
  item_type: string;
  item_description: string;
  quantity: number;
  unit_price: number;
  total_price: number;
}

interface Invoice {
  id: string;
  invoice_number: string;
  patient_id: string;
  total_amount: number;
  discount: number;
  tax: number;
  paid_amount: number;
  balance_amount: number;
  status: string;
  notes?: string;
  patient_name?: string;
  patient_code?: string;
  items: InvoiceItem[];
  created_at: string;
}

function statusBadge(s: string) {
  const map: Record<string, string> = {
    PENDING: 'badge-pending',
    PARTIAL: 'badge-partial',
    PAID: 'badge-paid',
    CANCELLED: 'badge-cancelled',
  };
  return <span className={`badge ${map[s] || 'badge-pending'}`}>{s}</span>;
}

export default function BillingPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Invoice | null>(null);
  const [filterStatus, setFilterStatus] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = { limit: '100' };
      if (filterStatus) params.status = filterStatus;
      const res = await api.get<Invoice[]>('/billing/invoices', { params });
      setInvoices(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [filterStatus]); // eslint-disable-line react-hooks/exhaustive-deps

  const fmt = (n: number) =>
    new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n);

  const totalBilled = invoices.reduce((s, i) => s + i.total_amount, 0);
  const totalCollected = invoices.reduce((s, i) => s + i.paid_amount, 0);
  const totalOutstanding = invoices.reduce((s, i) => s + i.balance_amount, 0);

  return (
    <DashboardLayout title="Billing" subtitle="Manage invoices and payments">
      <div className="page-header">
        <h1>Billing & Payments</h1>
        <p>Track invoices, payments and outstanding balances</p>
      </div>

      {/* Summary Cards */}
      <div className="stats-grid" style={{ marginBottom: '20px' }}>
        <div className="stat-card">
          <div className="stat-icon blue">💳</div>
          <div className="stat-info"><h3>{fmt(totalBilled)}</h3><p>Total Billed</p></div>
        </div>
        <div className="stat-card">
          <div className="stat-icon green">✅</div>
          <div className="stat-info"><h3>{fmt(totalCollected)}</h3><p>Total Collected</p></div>
        </div>
        <div className="stat-card">
          <div className="stat-icon yellow">⏳</div>
          <div className="stat-info"><h3>{fmt(totalOutstanding)}</h3><p>Outstanding</p></div>
        </div>
        <div className="stat-card">
          <div className="stat-icon teal">📄</div>
          <div className="stat-info"><h3>{invoices.length}</h3><p>Total Invoices</p></div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div className="flex gap-12">
            <select
              id="billing-filter-status"
              className="form-control"
              value={filterStatus}
              onChange={e => setFilterStatus(e.target.value)}
              style={{ width: 160 }}
            >
              <option value="">All Statuses</option>
              {['PENDING', 'PARTIAL', 'PAID', 'CANCELLED'].map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <button className="btn btn-secondary" onClick={load}>🔄 Refresh</button>
          </div>
        </div>

        <div className="table-wrap">
          {loading ? (
            <div className="loading-center"><div className="spinner" /><span>Loading invoices...</span></div>
          ) : invoices.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">💳</div>
              <p>No invoices found.</p>
            </div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Invoice #</th>
                  <th>Patient</th>
                  <th>Total</th>
                  <th>Paid</th>
                  <th>Balance</th>
                  <th>Status</th>
                  <th>Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map(inv => (
                  <tr key={inv.id}>
                    <td className="td-code">{inv.invoice_number}</td>
                    <td>
                      <div className="td-name">{inv.patient_name}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{inv.patient_code}</div>
                    </td>
                    <td style={{ fontWeight: 600 }}>{fmt(inv.total_amount)}</td>
                    <td style={{ color: 'var(--success)' }}>{fmt(inv.paid_amount)}</td>
                    <td style={{ color: inv.balance_amount > 0 ? 'var(--warning)' : 'var(--success)' }}>
                      {fmt(inv.balance_amount)}
                    </td>
                    <td>{statusBadge(inv.status)}</td>
                    <td>{new Date(inv.created_at).toLocaleDateString()}</td>
                    <td>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => setSelected(inv)}
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

      {/* Invoice Detail Modal */}
      {selected && (
        <div className="modal-overlay" onClick={() => setSelected(null)}>
          <div className="modal modal-lg" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Invoice – {selected.invoice_number}</h3>
              <button className="modal-close" onClick={() => setSelected(null)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="detail-grid" style={{ marginBottom: '16px' }}>
                <div className="detail-item"><label>Patient</label><span>{selected.patient_name}</span></div>
                <div className="detail-item"><label>Patient Code</label><span>{selected.patient_code}</span></div>
                <div className="detail-item"><label>Status</label><span>{statusBadge(selected.status)}</span></div>
                <div className="detail-item"><label>Date</label><span>{new Date(selected.created_at).toLocaleDateString()}</span></div>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <table>
                  <thead>
                    <tr>
                      <th>Description</th>
                      <th>Type</th>
                      <th>Qty</th>
                      <th>Unit Price</th>
                      <th>Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selected.items.map(it => (
                      <tr key={it.id}>
                        <td className="td-name">{it.item_description}</td>
                        <td><span className="badge badge-scheduled">{it.item_type}</span></td>
                        <td>{it.quantity}</td>
                        <td>{fmt(it.unit_price)}</td>
                        <td style={{ fontWeight: 600 }}>{fmt(it.total_price)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', alignItems: 'flex-end' }}>
                <div style={{ display: 'flex', gap: '40px' }}>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Subtotal:</span>
                  <span style={{ fontWeight: 600 }}>{fmt(selected.total_amount - selected.tax + selected.discount)}</span>
                </div>
                <div style={{ display: 'flex', gap: '40px' }}>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Tax:</span>
                  <span>{fmt(selected.tax)}</span>
                </div>
                <div style={{ display: 'flex', gap: '40px' }}>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Discount:</span>
                  <span style={{ color: 'var(--success)' }}>-{fmt(selected.discount)}</span>
                </div>
                <div style={{ display: 'flex', gap: '40px', borderTop: '1px solid var(--border)', paddingTop: '8px' }}>
                  <span style={{ fontWeight: 700 }}>Total:</span>
                  <span style={{ fontWeight: 700, fontSize: '18px' }}>{fmt(selected.total_amount)}</span>
                </div>
                <div style={{ display: 'flex', gap: '40px' }}>
                  <span style={{ color: 'var(--success)', fontSize: '13px' }}>Paid:</span>
                  <span style={{ color: 'var(--success)', fontWeight: 600 }}>{fmt(selected.paid_amount)}</span>
                </div>
                <div style={{ display: 'flex', gap: '40px' }}>
                  <span style={{ color: 'var(--warning)', fontSize: '13px' }}>Balance:</span>
                  <span style={{ color: 'var(--warning)', fontWeight: 700 }}>{fmt(selected.balance_amount)}</span>
                </div>
              </div>
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
