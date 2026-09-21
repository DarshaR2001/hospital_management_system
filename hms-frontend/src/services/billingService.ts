import api from '@/lib/api';
import { Invoice } from '@/types';

export const billingService = {
  listInvoices: (params?: { patient_id?: string; status?: string; limit?: number }) =>
    api.get<Invoice[]>('/billing/invoices', { params }).then(r => r.data),

  getInvoice: (id: string) =>
    api.get<Invoice>(`/billing/invoices/${id}`).then(r => r.data),

  createInvoice: (data: Record<string, unknown>) =>
    api.post<Invoice>('/billing/invoices', data).then(r => r.data),

  recordPayment: (id: string, amount: number, payment_method: string) =>
    api.post(`/billing/invoices/${id}/payment`, { amount, payment_method }).then(r => r.data),
};
