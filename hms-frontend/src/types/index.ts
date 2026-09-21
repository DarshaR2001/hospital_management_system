// Auth
export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthUser {
  access_token: string;
  token_type: string;
  role: string;
  user_id: string;
  email: string;
  full_name: string;
}

// Patient
export interface Patient {
  id: string;
  patient_code: string;
  first_name: string;
  last_name: string;
  gender: string;
  dob: string;
  blood_group?: string;
  phone: string;
  email?: string;
  address?: string;
  emergency_contact?: string;
  emergency_phone?: string;
  created_at: string;
  updated_at: string;
}

export interface PatientCreate {
  first_name: string;
  last_name: string;
  gender: string;
  dob: string;
  blood_group?: string;
  phone: string;
  email?: string;
  address?: string;
  emergency_contact?: string;
  emergency_phone?: string;
}

export interface PatientHistory extends Patient {
  appointments_count: number;
  medical_records_count: number;
  prescriptions_count: number;
  lab_requests_count: number;
  invoices_count: number;
  admissions_count: number;
}

// Appointment
export interface Appointment {
  id: string;
  appointment_number: string;
  patient_id: string;
  doctor_id: string;
  appointment_date: string;
  appointment_time: string;
  status: string;
  reason?: string;
  notes?: string;
  patient_name?: string;
  patient_code?: string;
  patient_phone?: string;
  doctor_name?: string;
  specialization?: string;
  consultation_fee?: number;
  created_at: string;
  updated_at: string;
}

export interface AppointmentCreate {
  patient_id: string;
  doctor_id: string;
  appointment_date: string;
  appointment_time: string;
  reason?: string;
  notes?: string;
}

// Staff
export interface Employee {
  id: string;
  employee_code: string;
  department: string;
  position: string;
  employment_type: string;
  hire_date: string;
  is_active: boolean;
  user: {
    id: string;
    full_name: string;
    email: string;
    phone?: string;
  };
  created_at: string;
}

export interface Doctor {
  id: string;
  specialization: string;
  qualification: string;
  license_number: string;
  consultation_fee: number;
  is_available: boolean;
  employee: {
    id: string;
    employee_code: string;
    department: string;
    user: {
      full_name: string;
      email: string;
    };
  };
}

// EMR
export interface MedicalRecord {
  id: string;
  patient_id: string;
  doctor_id: string;
  appointment_id?: string;
  chief_complaint: string;
  diagnosis: string;
  treatment_plan?: string;
  vital_signs?: Record<string, string>;
  notes?: string;
  patient_name?: string;
  doctor_name?: string;
  created_at: string;
}

export interface Prescription {
  id: string;
  patient_id: string;
  doctor_id: string;
  drug_name: string;
  dosage: string;
  frequency: string;
  duration: string;
  notes?: string;
  status: string;
  patient_name?: string;
  doctor_name?: string;
  created_at: string;
}

// Lab
export interface LabTestRequest {
  id: string;
  patient_id: string;
  doctor_id: string;
  test_name: string;
  urgency: string;
  status: string;
  notes?: string;
  result?: string;
  result_notes?: string;
  patient_name?: string;
  doctor_name?: string;
  created_at: string;
}

// Pharmacy
export interface Drug {
  id: string;
  name: string;
  generic_name: string;
  category: string;
  unit: string;
  stock_quantity: number;
  reorder_level: number;
  unit_price: number;
  is_active: boolean;
}

export interface Dispensing {
  id: string;
  patient_id: string;
  drug_id: string;
  prescription_id?: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  patient_name?: string;
  drug_name?: string;
  dispensed_by_name?: string;
  created_at: string;
}

// Billing
export interface Invoice {
  id: string;
  invoice_number: string;
  patient_id: string;
  appointment_id?: string;
  total_amount: number;
  paid_amount: number;
  status: string;
  due_date?: string;
  patient_name?: string;
  items?: InvoiceItem[];
  created_at: string;
}

export interface InvoiceItem {
  id: string;
  description: string;
  quantity: number;
  unit_price: number;
  total: number;
}

// Inpatient
export interface Admission {
  id: string;
  patient_id: string;
  doctor_id: string;
  ward_name: string;
  bed_number: string;
  admission_date: string;
  discharge_date?: string;
  diagnosis: string;
  status: string;
  notes?: string;
  patient_name?: string;
  doctor_name?: string;
  created_at: string;
}

export interface Ward {
  id: string;
  name: string;
  ward_type: string;
  total_beds: number;
  available_beds: number;
  is_active: boolean;
}
