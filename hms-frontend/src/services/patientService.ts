import api from '@/lib/api';
import { Patient, PatientCreate, PatientHistory } from '@/types';

export const patientService = {
  list: (q?: string, limit = 50, offset = 0) =>
    api.get<Patient[]>('/patients', { params: { q, limit, offset } }).then(r => r.data),

  get: (id: string) =>
    api.get<Patient>(`/patients/${id}`).then(r => r.data),

  history: (id: string) =>
    api.get<PatientHistory>(`/patients/${id}/history`).then(r => r.data),

  create: (data: PatientCreate) =>
    api.post<Patient>('/patients', data).then(r => r.data),

  update: (id: string, data: Partial<PatientCreate>) =>
    api.put<Patient>(`/patients/${id}`, data).then(r => r.data),

  delete: (id: string) =>
    api.delete(`/patients/${id}`).then(r => r.data),
};
