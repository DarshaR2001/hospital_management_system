import api from '@/lib/api';
import { Appointment, AppointmentCreate } from '@/types';

export const appointmentService = {
  list: (params?: {
    appointment_date?: string;
    doctor_id?: string;
    patient_id?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }) =>
    api.get<Appointment[]>('/appointments', { params }).then(r => r.data),

  get: (id: string) =>
    api.get<Appointment>(`/appointments/${id}`).then(r => r.data),

  create: (data: AppointmentCreate) =>
    api.post<Appointment>('/appointments', data).then(r => r.data),

  updateStatus: (id: string, status: string, notes?: string) =>
    api.patch<Appointment>(`/appointments/${id}/status`, { status, notes }).then(r => r.data),

  reschedule: (id: string, appointment_date: string, appointment_time: string, notes?: string) =>
    api.put<Appointment>(`/appointments/${id}/reschedule`, {
      appointment_date,
      appointment_time,
      notes,
    }).then(r => r.data),
};
