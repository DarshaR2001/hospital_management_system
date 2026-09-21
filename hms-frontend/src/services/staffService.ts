import api from '@/lib/api';
import { Employee, Doctor } from '@/types';

export const staffService = {
  listEmployees: (params?: { q?: string; department?: string; limit?: number }) =>
    api.get<Employee[]>('/staff/employees', { params }).then(r => r.data),

  listDoctors: (params?: { specialization?: string; is_available?: boolean }) =>
    api.get<Doctor[]>('/staff/doctors', { params }).then(r => r.data),

  getEmployee: (id: string) =>
    api.get<Employee>(`/staff/employees/${id}`).then(r => r.data),

  getDoctor: (id: string) =>
    api.get<Doctor>(`/staff/doctors/${id}`).then(r => r.data),

  createEmployee: (data: Record<string, unknown>) =>
    api.post<Employee>('/staff/employees', data).then(r => r.data),

  createDoctor: (data: Record<string, unknown>) =>
    api.post<Doctor>('/staff/doctors', data).then(r => r.data),

  updateEmployee: (id: string, data: Record<string, unknown>) =>
    api.put<Employee>(`/staff/employees/${id}`, data).then(r => r.data),
};
