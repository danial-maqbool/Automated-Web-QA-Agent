export interface Project {
  id: string;
  name: string;
  base_url: string;
  description?: string;
  allowed_domains: string[];
  tags: string[];
  created_at: string;
  environments: Environment[];
  ignore_rules: IgnoreRule[];
}

export interface Environment {
  id: string;
  project_id: string;
  name: string;
  base_url: string;
  crawl_depth: number;
  max_pages: number;
  timeout_ms: number;
  is_default: boolean;
}

export interface IgnoreRule {
  id: string;
  project_id: string;
  rule_type: string;
  pattern: string;
  reason?: string;
  is_active: boolean;
}

export interface QARun {
  id: string;
  project_id: string;
  environment_id?: string;
  scan_type: string;
  status: string; // PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
  trigger: string;
  browser: string;
  viewport_width: number;
  viewport_height: number;
  
  pages_discovered: number;
  pages_tested: number;
  total_issues: number;
  critical_issues: number;
  high_issues: number;
  medium_issues: number;
  low_issues: number;
  info_issues: number;
  qa_score: number;

  new_issues_count: number;
  existing_issues_count: number;
  resolved_issues_count: number;
  regression_issues_count: number;

  current_url?: string;
  current_action?: string;
  error_message?: string;

  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface RunEvent {
  id: string;
  run_id: string;
  timestamp: string;
  level: string; // INFO, WARNING, ERROR, SUCCESS
  message: string;
  url?: string;
}

export interface Issue {
  id: string;
  project_id: string;
  fingerprint: string;
  title: string;
  category: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO";
  confidence: number;
  status: "OPEN" | "ACKNOWLEDGED" | "FIXED" | "IGNORED" | "REGRESSION";
  description: string;
  page_url: string;
  selector?: string;
  expected_behavior?: string;
  observed_behavior?: string;
  reproduction_steps: Array<{ action: string; target?: string; value?: string }>;
  screenshot_path?: string;
  trace_path?: string;
  network_evidence?: any;
  console_evidence?: any;
  browser: string;
  viewport: string;
  occurrence_count: number;
  affected_pages_count: number;
  affected_pages: string[];
  notes?: string;
  first_detected_at: string;
  last_detected_at: string;
}

export interface PageRecord {
  id: string;
  project_id: string;
  url: string;
  path: string;
  title?: string;
  status_code?: number;
  load_time_ms?: number;
  screenshot_path?: string;
  last_tested_at?: string;
}

export interface Baseline {
  id: string;
  project_id: string;
  page_url: string;
  viewport: string;
  browser: string;
  screenshot_path: string;
  is_active: boolean;
  created_at: string;
}

export interface TestScenario {
  id: string;
  project_id: string;
  name: string;
  description?: string;
  is_active: boolean;
  tags: string[];
  steps: Array<{
    id?: string;
    order_index: number;
    action_type: string;
    target?: string;
    value?: string;
    expected_value?: string;
    is_optional: boolean;
  }>;
}
