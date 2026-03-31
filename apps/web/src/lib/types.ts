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
}

export interface StreamEnvelope {
	type: "event" | "state";
	state: DashboardState;
	event: RawEventRecord | null;
}
