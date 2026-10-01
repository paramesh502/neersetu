export interface Farmer {
  id: number;
  farmer_id: string;
  name: string;
  phone: string;
  plot_number: string;
  canal_position: number;
  crop_type: string;
  flow_efficiency_index: number;
  water_credit_balance: number;
  total_hours_allocated: number;
  total_hours_used: number;
  historical_deficit: number;
  missed_turns: number;
}

export interface Schedule {
  id: number;
  farmer_id: number;
  farmer_name?: string;
  farmer_plot?: string;
  slot_start: string;
  slot_end: string;
  hours_allocated: number;
  hours_used: number;
  status: string;
  notes?: string;
}

export interface EmergencyRequest {
  id: number;
  farmer_id: number;
  farmer_name?: string;
  farmer_plot?: string;
  raw_message: string;
  extracted_crop?: string;
  extracted_urgency?: string;
  extracted_hours?: number;
  extracted_plot?: string;
  status: string;
  fwos_score?: number;
  resolution_summary?: string;
  decision_trace?: string;
  created_at: string;
}

export interface AgentStep {
  agent: string;
  status: string;
  output: string;
  details: Record<string, unknown>;
}

export interface PipelineResult {
  emergency_request_id: number;
  status: string;
  fwos_score?: number;
  consent_decision?: string;
  consent_reason?: string;
  proposal_text?: string;
  chat_notification?: string;
  sms_notification?: string;
  ivr_script?: string;
  print_schedule?: string;
  fairness_explanation?: string;
  credit_id?: string;
  compensation_hours?: number;
  hours_yielded?: number;
  yielding_farmer_name?: string;
  fwos_breakdown?: FWOSBreakdown;
  agent_steps: AgentStep[];
  error?: string;
}

export interface FWOSBreakdown {
  downstream_penalty: number;
  efficiency_deficit: number;
  historical_deficit_score: number;
  missed_turns_score: number;
  crop_urgency_score: number;
  total: number;
  inputs: {
    canal_position: number;
    max_position: number;
    eta: number;
    historical_deficit: number;
    missed_turns: number;
    urgency: string;
  };
}

export interface Negotiation {
  id: number;
  emergency_request_id?: number;
  requesting_farmer_name?: string;
  requesting_farmer_plot?: string;
  yielding_farmer_name?: string;
  yielding_farmer_plot?: string;
  hours_requested: number;
  hours_yielded: number;
  compensation_hours: number;
  yielding_farmer_eta: number;
  receiving_farmer_eta: number;
  proposal_text: string;
  status: string;
  agent_steps?: AgentStep[];
  created_at: string;
}

export interface WaterCredit {
  id: number;
  credit_id: string;
  giving_farmer_id?: number;
  giving_farmer_name?: string;
  receiving_farmer_id?: number;
  receiving_farmer_name?: string;
  hours_given: number;
  hours_owed: number;
  status: string;
  notes?: string;
  created_at: string;
  redeemed_at?: string;
}

export interface AuditEntry {
  id: number;
  event_type: string;
  actor: string;
  description: string;
  metadata_json?: string;
  timestamp: string;
}

export interface DashboardData {
  summary: {
    total_farmers: number;
    active_emergency_requests: number;
    active_credits: number;
    total_credit_hours_owed: number;
    recent_negotiations: number;
  };
  active_farmer: { name: string; plot: string; eta: number } | null;
  upcoming_schedule: {
    schedule_id: number;
    farmer_name: string;
    plot: string;
    eta: number;
    slot_start: string;
    slot_end: string;
    hours: number;
    status: string;
  }[];
  farmer_cards: {
    farmer_id: string;
    name: string;
    plot: string;
    canal_position: number;
    crop_type: string;
    eta: number;
    fwos: number;
    credit_balance: number;
    historical_deficit: number;
    missed_turns: number;
  }[];
  emergency_requests: {
    id: number;
    farmer_id: number;
    status: string;
    urgency?: string;
    crop?: string;
    created_at: string;
  }[];
  canal_flow: {
    position: number;
    plot: string;
    farmer: string;
    eta: number;
    flow_percent: number;
  }[];
}
