import api from '@/lib/api';
import { Admission, Ward } from '@/types';

export const inpatientService = {
  listAdmissions: (params?: { status?: string; ward_id?: string; limit?: number }) =>
    api.get<Admission[]>('/inpatient/admissions', { params }).then(r => r.data),

  getAdmission: (id: string) =>
    api.get<Admission>(`/inpatient/admissions/${id}`).then(r => r.data),

  createAdmission: (data: Record<string, unknown>) =>
    api.post<Admission>('/inpatient/admissions', data).then(r => r.data),

  discharge: (id: string, data: Record<string, unknown>) =>
    api.patch<Admission>(`/inpatient/admissions/${id}/discharge`, data).then(r => r.data),

  listWards: () =>
    api.get<Ward[]>('/inpatient/wards').then(r => r.data),
};
