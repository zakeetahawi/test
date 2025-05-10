export interface InstallationStep {
  id: string;
  name: string;
  status: 'pending' | 'in_progress' | 'completed' | 'delayed' | 'failed';
  startTime?: Date;
  endTime?: Date;
  duration?: number;
  notes?: string;
}

export interface InstallationIssue {
  id: string;
  type: 'technical' | 'customer' | 'team' | 'other';
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'open' | 'in_progress' | 'resolved';
  createdAt: Date;
  resolvedAt?: Date;
}

export interface InstallationUpdate {
  installationId: string;
  currentStep: InstallationStep;
  progress: number;
  estimatedTimeRemaining?: number;
  issues: InstallationIssue[];
  lastUpdate: Date;
  teamLocation?: {
    lat: number;
    lng: number;
  };
}

export interface InstallationTimelineEvent {
  id: string;
  type: 'step_change' | 'issue_reported' | 'issue_resolved' | 'team_update' | 'delay_reported';
  timestamp: Date;
  title: string;
  description: string;
  severity?: 'info' | 'warning' | 'error' | 'success';
}