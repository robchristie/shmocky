export interface ConnectionState {
	backend_online: boolean;
	codex_connected: boolean;
	initialized: boolean;
	app_server_pid: number | null;
	app_server_user_agent: string | null;
	codex_home: string | null;
	platform_family: string | null;
	platform_os: string | null;
	last_error: string | null;
}

export interface ThreadState {
	id: string;
	status: string;
	cwd: string | null;
	model: string | null;
	model_provider: string | null;
	approval_policy: string | null;
	sandbox_mode: string | null;
	reasoning_effort: string | null;
	created_at: number | null;
	updated_at: number | null;
}

export interface TurnState {
	id: string;
	status: string;
	last_event_at: string | null;
	error: string | null;
}

export interface TranscriptItem {
	item_id: string;
	role: "user" | "assistant";
	text: string;
	phase: string | null;
	status: "streaming" | "completed";
	turn_id: string | null;
}

export interface PendingServerRequest {
	request_id: string;
	method: string;
	params: Record<string, unknown> | null;
	noted_at: string;
}

export interface DashboardState {
	workspace_root: string;
	event_log_path: string;
	connection: ConnectionState;
	thread: ThreadState | null;
	turn: TurnState | null;
	transcript: TranscriptItem[];
	mcp_servers: Record<string, string>;
	rate_limits: Record<string, unknown> | null;
	pending_server_request: PendingServerRequest | null;
	workflow_run: WorkflowRunState | null;
}

export interface RawEventRecord {
	sequence: number;
	event_id: string;
	recorded_at: string;
	direction: "outbound" | "inbound" | "internal";
	channel: "rpc" | "stderr" | "lifecycle";
	message_type:
		| "request"
		| "response"
		| "notification"
		| "server_request"
		| "stderr"
		| "lifecycle"
		| "unknown";
	method: string | null;
	payload: unknown;
}

export interface DashboardSnapshot {
	state: DashboardState;
	recent_events: RawEventRecord[];
	recent_workflow_events: WorkflowEventRecord[];
}

export interface StreamEnvelope {
	type: "event" | "workflow_event" | "state";
	state: DashboardState;
	event: RawEventRecord | null;
	workflow_event: WorkflowEventRecord | null;
}

export interface AgentDefinition {
	id: string;
	provider: "codex" | "oracle";
	role: string;
	startup_prompt: string | null;
	description: string | null;
	model: string | null;
	model_provider: string | null;
	reasoning_effort: string | null;
	approval_policy: string | null;
	sandbox_mode: string | null;
	web_access: "disabled" | "cached" | "live" | null;
	service_tier: "fast" | "flex" | null;
	remote_host: string | null;
	chatgpt_url: string | null;
	model_strategy: "current" | "ignore" | null;
	timeout_seconds: number | null;
}

export interface WorkflowDefinition {
	id: string;
	kind: "linear_loop";
	planner_agent: string;
	executor_agent: string;
	expert_agent: string | null;
	judge_agent: string;
	plan_prompt_template: string;
	execute_prompt_template: string;
	expert_prompt_template: string | null;
	judge_prompt_template: string;
	max_loops: number;
	max_runtime_minutes: number;
	max_judge_calls: number;
}

export interface WorkflowCatalogResponse {
	config_path: string;
	loaded: boolean;
	error: string | null;
	agents: AgentDefinition[];
	workflows: WorkflowDefinition[];
}

export interface OracleResumeCheckpoint {
	agent_label: "expert" | "judge";
	agent_id: string;
	thread_id: string;
	loop_index: number;
	prompt: string;
	detail: string | null;
	noted_at: string;
}

export interface RunHistoryEntry {
	id: string;
	run_name: string | null;
	workflow_id: string;
	target_dir: string;
	execution_dir: string | null;
	status:
		| "idle"
		| "starting"
		| "running"
		| "paused"
		| "completed"
		| "failed"
		| "stopped";
	phase:
		| "idle"
		| "planning"
		| "executing"
		| "advising"
		| "judging"
		| "paused"
		| "completed"
		| "failed"
		| "stopped";
	started_at: string;
	updated_at: string;
	completed_at: string | null;
	last_judge_decision: "continue" | "complete" | "fail" | null;
	last_judge_summary: string | null;
	last_error: string | null;
}

export interface RunHistoryResponse {
	runs: RunHistoryEntry[];
}

export interface WorkflowRunState {
	id: string;
	run_name: string | null;
	workflow_id: string;
	target_dir: string;
	execution_dir: string | null;
	workspace_strategy: "git_worktree" | null;
	worktree_branch: string | null;
	worktree_base_commit: string | null;
	goal: string;
	status:
		| "idle"
		| "starting"
		| "running"
		| "paused"
		| "completed"
		| "failed"
		| "stopped";
	phase:
		| "idle"
		| "planning"
		| "executing"
		| "advising"
		| "judging"
		| "paused"
		| "completed"
		| "failed"
		| "stopped";
	codex_agent_id: string;
	judge_agent_id: string;
	started_at: string;
	updated_at: string;
	completed_at: string | null;
	current_loop: number;
	max_loops: number;
	judge_calls: number;
	max_judge_calls: number;
	max_runtime_minutes: number;
	expert_agent_id: string | null;
	last_plan: string | null;
	last_codex_output: string | null;
	last_expert_assessment: string | null;
	last_judge_decision: "continue" | "complete" | "fail" | null;
	last_judge_summary: string | null;
	last_continuation_prompt: string | null;
	oracle_resume_checkpoint: OracleResumeCheckpoint | null;
	last_error: string | null;
	pause_requested: boolean;
	stop_requested: boolean;
	pending_steering_notes: string[];
	recent_steering_notes: string[];
}

export interface WorkflowEventRecord {
	sequence: number;
	event_id: string;
	recorded_at: string;
	kind: string;
	message: string;
	payload: unknown;
}
