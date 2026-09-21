'use client';

import { useEffect, useState } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import api from '@/lib/api';

interface Drug {
  id: string;
  name: string;
  generic_name: string;
  drug_type: string;
  unit: string;
  unit_price: number;
  is_active: boolean;
  reorder_level: number;
  batches: DrugBatch[];
  total_stock?: number;
}

interface DrugBatch {
  id: string;
  batch_number: string;
  quantity: number;
  expiry_date: string;
  purchase_price: number;
}

interface Dispensing {
  id: string;
  dispensing_number: string;
  patient_name?: string;
  patient_code?: string;
  items: DispensingItem[];
  dispensed_by_name?: string;
  created_at: string;
  total_amount: number;
}

interface DispensingItem {
  id: string;
  drug_name?: string;
  quantity: number;
  unit_price: number;
  total_price: number;
}

export default function PharmacyPage() {
  const [tab, setTab] = useState<'inventory' | 'dispensing'>('inventory');
  const [drugs, setDrugs] = useState<Drug[]>([]);
  const [dispensing, setDispensing] = useState<Dispensing[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      try {
        const [drugRes, dispRes] = await Promise.all([
          api.get<Drug[]>('/pharmacy/medicines'),
          api.get<Dispensing[]>('/pharmacy/dispensing', { params: { limit: 100 } }),
        ]);
        const drugsWithStock = drugRes.data.map(d => ({
          ...d,
          total_stock: d.batches?.reduce((s, b) => s + b.quantity, 0) ?? 0,
        }));
        setDrugs(drugsWithStock);
        setDispensing(dispRes.data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  const lowStockCount = drugs.filter(d => (d.total_stock ?? 0) <= d.reorder_level).length;

  const fmt = (n: number) =>
    new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n);

  return (
    <DashboardLayout title="Pharmacy" subtitle="Drug inventory and dispensing">
      <div className="page-header">
        <h1>Pharmacy Management</h1>
        <p>Manage drug inventory and patient dispensing records</p>
      </div>

      {/* Summary stats */}
      <div className="stats-grid" style={{ marginBottom: '20px' }}>
        <div className="stat-card">
          <div className="stat-icon teal">💊</div>
          <div className="stat-info"><h3>{drugs.length}</h3><p>Total Medicines</p></div>
        </div>
        <div className="stat-card">
          <div className="stat-icon red">⚠️</div>
          <div className="stat-info"><h3>{lowStockCount}</h3><p>Low Stock Items</p></div>
        </div>
        <div className="stat-card">
          <div className="stat-icon blue">📦</div>
          <div className="stat-info"><h3>{dispensing.length}</h3><p>Dispensing Records</p></div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '4px', marginBottom: '20px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius)', padding: '4px', width: 'fit-content' }}>
        <button
          id="tab-inventory"
          className={`btn ${tab === 'inventory' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setTab('inventory')}
        >
          💊 Inventory ({drugs.length})
        </button>
        <button
          id="tab-dispensing"
          className={`btn ${tab === 'dispensing' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setTab('dispensing')}
        >
          📦 Dispensing ({dispensing.length})
        </button>
      </div>

      <div className="card">
        <div className="table-wrap">
          {loading ? (
            <div className="loading-center"><div className="spinner" /><span>Loading...</span></div>
          ) : tab === 'inventory' ? (
            drugs.length === 0 ? (
              <div className="empty-state"><div className="empty-icon">💊</div><p>No medicines in inventory.</p></div>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Generic Name</th>
                    <th>Type</th>
                    <th>Unit</th>
                    <th>Stock</th>
                    <th>Reorder Level</th>
                    <th>Unit Price</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {drugs.map(d => {
                    const isLow = (d.total_stock ?? 0) <= d.reorder_level;
                    return (
                      <tr key={d.id}>
                        <td className="td-name">{d.name}</td>
                        <td style={{ color: 'var(--text-secondary)' }}>{d.generic_name}</td>
                        <td><span className="badge badge-scheduled">{d.drug_type}</span></td>
                        <td>{d.unit}</td>
                        <td style={{ fontWeight: 700, color: isLow ? 'var(--danger)' : 'var(--success)' }}>
                          {d.total_stock ?? 0} {isLow && '⚠️'}
                        </td>
                        <td>{d.reorder_level}</td>
                        <td>{fmt(d.unit_price)}</td>
                        <td>
                          <span className={`badge ${d.is_active ? 'badge-active' : 'badge-inactive'}`}>
                            {d.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )
          ) : (
            dispensing.length === 0 ? (
              <div className="empty-state"><div className="empty-icon">📦</div><p>No dispensing records found.</p></div>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Dispensing #</th>
                    <th>Patient</th>
                    <th>Items</th>
                    <th>Total</th>
                    <th>Dispensed By</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {dispensing.map(d => (
                    <tr key={d.id}>
                      <td className="td-code">{d.dispensing_number}</td>
                      <td>
                        <div className="td-name">{d.patient_name}</div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{d.patient_code}</div>
                      </td>
                      <td>{d.items?.length ?? 0} item(s)</td>
                      <td style={{ fontWeight: 600, color: 'var(--accent)' }}>{fmt(d.total_amount)}</td>
                      <td>{d.dispensed_by_name || '—'}</td>
                      <td>{new Date(d.created_at).toLocaleDateString()}</td>
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
