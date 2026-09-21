import api from '@/lib/api';
import { LabTestRequest } from '@/types';

export const labService = {
  listRequests: (params?: { patient_id?: string; status?: string; limit?: number }) =>
    api.get<LabTestRequest[]>('/lab/requests', { params }).then(r => r.data),

  getRequest: (id: string) =>
    api.get<LabTestRequest>(`/lab/requests/${id}`).then(r => r.data),

  createRequest: (data: Record<string, unknown>) =>
    api.post<LabTestRequest>('/lab/requests', data).then(r => r.data),

  updateResult: (id: string, result: string, result_notes?: string) =>
    api.patch<LabTestRequest>(`/lab/requests/${id}/result`, { result, result_notes }).then(r => r.data),

  updateStatus: (id: string, status: string) =>
    api.patch<LabTestRequest>(`/lab/requests/${id}/status`, { status }).then(r => r.data),
};
