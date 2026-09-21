import api from '@/lib/api';
import { Drug, Dispensing } from '@/types';

export const pharmacyService = {
  listDrugs: (params?: { q?: string; low_stock?: boolean }) =>
    api.get<Drug[]>('/pharmacy/drugs', { params }).then(r => r.data),

  getDrug: (id: string) =>
    api.get<Drug>(`/pharmacy/drugs/${id}`).then(r => r.data),

  createDrug: (data: Record<string, unknown>) =>
    api.post<Drug>('/pharmacy/drugs', data).then(r => r.data),

  updateStock: (id: string, quantity: number) =>
    api.patch<Drug>(`/pharmacy/drugs/${id}/stock`, { quantity }).then(r => r.data),

  listDispensing: (params?: { patient_id?: string; limit?: number }) =>
    api.get<Dispensing[]>('/pharmacy/dispensing', { params }).then(r => r.data),

  dispense: (data: Record<string, unknown>) =>
    api.post<Dispensing>('/pharmacy/dispensing', data).then(r => r.data),
};
