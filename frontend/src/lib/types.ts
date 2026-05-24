export interface User {
  id: string;
  email: string;
  name: string;
  phone: string;
  role: 'owner' | 'admin';
  created_at: string;
}

export interface Store {
  id: string;
  owner_id: string;
  name: string;
  address?: string;
  latitude?: number;
  longitude?: number;
  created_at: string;
}

export interface Camera {
  id: string;
  store_id: string;
  name: string;
  rtsp_url: string;
  location_hint?: string;
  status: 'online' | 'offline' | 'maintenance';
  last_seen?: string;
  config?: string;
}

export interface Event {
  id: string;
  camera_id: string;
  store_id: string;
  event_type: 'shoplifting_suspected' | 'motion_anomaly' | 'object_left' | 'restricted_area_breach' | 'cash_register_theft';
  confidence: number;
  description: string;
  clip_path?: string;
  thumbnail_path?: string;
  created_at: string;
}

export interface Alert {
  id: string;
  event_id: string;
  user_id: string;
  channel: 'sms' | 'push' | 'email';
  status: 'pending' | 'sent' | 'failed';
  sent_at?: string;
  twilio_sid?: string;
}
