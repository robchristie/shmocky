<script lang="ts">
import { onMount, tick } from "svelte";
import { fade } from "svelte/transition";
import { Button } from "$lib/components/ui/button";
import { Textarea } from "$lib/components/ui/textarea";
import type {
	DashboardSnapshot,
	DashboardState,
	RawEventRecord,
	RunHistoryEntry,
	RunHistoryResponse,
	StreamEnvelope,
	WorkflowCatalogResponse,
	WorkflowDefinition,
	WorkflowEventRecord,
} from "$lib/types";

type EventStreamEntry = {
	id: string;
	recordedAt: string;
	method: string | null;
	messageType: RawEventRecord["message_type"];
	summary: string;
	chunkCount: number;
};

type DerivedTranscriptEntry = {
	id: string;
	speaker: string;
	title: string;
	body: string;
	tone: "default" | "muted";
};

type EventStreamMode = "coalesced" | "important" | "raw";
type OperatorRailTab = "run" | "activity" | "protocol";

type PendingQuestionOption = {
	label: string;
	description: string;
};

type PendingUserInputQuestion = {
	header: string;
	id: string;
	question: string;
	options?: PendingQuestionOption[] | null;
	isOther?: boolean;
	isSecret?: boolean;
};

type PendingRequestAction = {
	label: string;
	result: unknown;
	variant: "default" | "secondary" | "outline" | "destructive";
};

let dashboardState: DashboardState | null = $state(null);
let workflowCatalog: WorkflowCatalogResponse | null = $state(null);
let recentEvents: RawEventRecord[] = $state([]);
let recentWorkflowEvents: WorkflowEventRecord[] = $state([]);
let runHistory: RunHistoryEntry[] = $state([]);
let historicalSnapshot: DashboardSnapshot | null = $state(null);
let loading = $state(true);
let requestError: string | null = $state(null);
let socketState: "connecting" | "open" | "closed" = $state("connecting");
let selectedRunView = $state("live");
let selectedWorkflowId = $state("");
let runName = $state("");
let targetDir = $state("");
let startPrompt = $state("");
let steerNote = $state("");
let startingRun = $state(false);
let pausingRun = $state(false);
let resumingRun = $state(false);
let stoppingRun = $state(false);
let steeringRun = $state(false);
let resolvingServerRequest = $state(false);
let customServerRequestResponse = $state("");
let userInputDrafts = $state<Record<string, string>>({});
let pendingRequestSeedKey = $state("");
let transcriptPane: HTMLDivElement | null = $state(null);
let workflowPane: HTMLDivElement | null = $state(null);
let eventPane: HTMLDivElement | null = $state(null);
let autoScrollTranscript = $state(true);
let autoScrollWorkflowEvents = $state(true);
let autoScrollEvents = $state(true);
let eventStreamMode: EventStreamMode = $state("important");
let operatorRailTab: OperatorRailTab = $state("run");
let reconnectTimer: number | null = null;
let socket: WebSocket | null = null;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
	const response = await fetch(path, {
		headers: {
			"content-type": "application/json",
		},
		...init,
	});
	if (!response.ok) {
		throw new Error(await response.text());
	}
	return (await response.json()) as T;
}

function activeRun() {
	return viewedState()?.workflow_run ?? null;
}

function liveRun() {
	return dashboardState?.workflow_run ?? null;
}

function livePendingRequest() {
	return dashboardState?.pending_server_request ?? null;
}

function viewedState(): DashboardState | null {
	return historicalSnapshot?.state ?? dashboardState;
}

function viewedRecentEvents(): RawEventRecord[] {
	return historicalSnapshot?.recent_events ?? recentEvents;
}

function viewedRecentWorkflowEvents(): WorkflowEventRecord[] {
	return historicalSnapshot?.recent_workflow_events ?? recentWorkflowEvents;
}

function applySnapshot(snapshot: DashboardSnapshot) {
	dashboardState = snapshot.state;
	recentEvents = snapshot.recent_events;
	recentWorkflowEvents = snapshot.recent_workflow_events;
	loading = false;
	requestError = null;
}

function applyEnvelope(payload: StreamEnvelope | DashboardSnapshot) {
	if ("type" in payload) {
		dashboardState = payload.state;
		loading = false;
		requestError = null;
		if (payload.type === "event" && payload.event) {
			recentEvents = [...recentEvents, payload.event].slice(-300);
		}
		if (payload.type === "workflow_event" && payload.workflow_event) {
			recentWorkflowEvents = [
				...recentWorkflowEvents,
				payload.workflow_event,
			].slice(-200);
			if (
				payload.workflow_event.kind === "run_started" ||
				payload.workflow_event.kind === "run_completed" ||
				payload.workflow_event.kind === "run_failed" ||
				payload.workflow_event.kind === "run_stopped"
			) {
				void refreshRuns();
			}
		}
		return;
	}
	applySnapshot(payload);
}

async function refreshState() {
	try {
		const snapshot = await request<DashboardSnapshot>("/api/state");
		applySnapshot(snapshot);
	} catch (error) {
		requestError = toErrorMessage(error);
		loading = false;
	}
}

async function refreshWorkflows() {
	try {
		const catalog = await request<WorkflowCatalogResponse>("/api/workflows");
		workflowCatalog = catalog;
		if (!selectedWorkflowId && catalog.workflows.length > 0) {
			selectedWorkflowId = catalog.workflows[0].id;
		}
	} catch (error) {
		requestError = toErrorMessage(error);
	}
}

async function refreshRuns() {
	try {
		const response = await request<RunHistoryResponse>("/api/runs");
		runHistory = response.runs;
	} catch (error) {
		requestError = toErrorMessage(error);
	}
}

async function selectRunView(runId: string) {
	selectedRunView = runId;
	if (runId === "live") {
		historicalSnapshot = null;
		requestError = null;
		return;
	}
	try {
		historicalSnapshot = await request<DashboardSnapshot>(
			`/api/runs/${encodeURIComponent(runId)}`,
		);
		requestError = null;
	} catch (error) {
		requestError = toErrorMessage(error);
	}
}

async function startWorkflowRun() {
	if (!selectedWorkflowId || !targetDir.trim() || !startPrompt.trim()) {
		return;
	}
	startingRun = true;
	try {
		const snapshot = await request<DashboardSnapshot>("/api/runs", {
			method: "POST",
			body: JSON.stringify({
				run_name: runName.trim() || null,
				workflow_id: selectedWorkflowId,
				target_dir: targetDir.trim(),
				prompt: startPrompt.trim(),
			}),
		});
		applySnapshot(snapshot);
		runName = "";
		startPrompt = "";
		steerNote = "";
		await refreshRuns();
	} catch (error) {
		requestError = toErrorMessage(error);
	} finally {
		startingRun = false;
	}
}

async function pauseRun() {
	pausingRun = true;
	try {
		const snapshot = await request<DashboardSnapshot>(
			"/api/runs/active/pause",
			{
				method: "POST",
			},
		);
		applySnapshot(snapshot);
	} catch (error) {
		requestError = toErrorMessage(error);
	} finally {
		pausingRun = false;
	}
}

async function resumeRun() {
	resumingRun = true;
	try {
		const snapshot = await request<DashboardSnapshot>(
			"/api/runs/active/resume",
			{
				method: "POST",
			},
		);
		applySnapshot(snapshot);
	} catch (error) {
		requestError = toErrorMessage(error);
	} finally {
		resumingRun = false;
	}
}

async function stopRun() {
	stoppingRun = true;
	try {
		const snapshot = await request<DashboardSnapshot>("/api/runs/active/stop", {
			method: "POST",
		});
		applySnapshot(snapshot);
	} catch (error) {
		requestError = toErrorMessage(error);
	} finally {
		stoppingRun = false;
	}
}

async function queueSteer() {
	if (!steerNote.trim()) {
		return;
	}
	steeringRun = true;
	try {
		const snapshot = await request<DashboardSnapshot>(
			"/api/runs/active/steer",
			{
				method: "POST",
				body: JSON.stringify({ note: steerNote.trim() }),
			},
		);
		applySnapshot(snapshot);
		steerNote = "";
	} catch (error) {
		requestError = toErrorMessage(error);
	} finally {
		steeringRun = false;
	}
}

async function resolvePendingServerRequest(result: unknown) {
	const pending = livePendingRequest();
	if (!pending) {
		return;
	}
	resolvingServerRequest = true;
	try {
		const snapshot = await request<DashboardSnapshot>(
			`/api/server-requests/${encodeURIComponent(pending.request_id)}/resolve`,
			{
				method: "POST",
				body: JSON.stringify({ result }),
			},
		);
		applySnapshot(snapshot);
	} catch (error) {
		requestError = toErrorMessage(error);
	} finally {
		resolvingServerRequest = false;
	}
}

async function submitCustomServerRequestResponse() {
	let result: unknown = null;
	if (customServerRequestResponse.trim()) {
		try {
			result = JSON.parse(customServerRequestResponse);
		} catch (error) {
			requestError = `Invalid response JSON: ${toErrorMessage(error)}`;
			return;
		}
	}
	await resolvePendingServerRequest(result);
}

function setUserInputDraft(questionId: string, value: string) {
	userInputDrafts = {
		...userInputDrafts,
		[questionId]: value,
	};
}

function parseDelimitedAnswers(value: string): string[] {
	return value
		.split(/\n|,/)
		.map((entry) => entry.trim())
		.filter(Boolean);
}

async function submitPendingUserInput() {
	const pending = livePendingRequest();
	const questions = pendingRequestQuestions(pending);
	if (!pending || !questions.length) {
		return;
	}
	const answers: Record<string, { answers: string[] }> = {};
	for (const question of questions) {
		const parsed = parseDelimitedAnswers(userInputDrafts[question.id] ?? "");
		if (!parsed.length) {
			requestError = `Answer required for ${question.header}.`;
			return;
		}
		answers[question.id] = { answers: parsed };
	}
	await resolvePendingServerRequest({ answers });
}

function connectStream() {
	socketState = "connecting";
	socket = new WebSocket(
		`${window.location.origin.replace("http", "ws")}/api/events`,
	);
	socket.addEventListener("open", () => {
		socketState = "open";
	});
	socket.addEventListener("message", (event) => {
		try {
			const payload = JSON.parse(event.data) as
				| StreamEnvelope
				| DashboardSnapshot;
			applyEnvelope(payload);
		} catch (error) {
			requestError = toErrorMessage(error);
		}
	});
	socket.addEventListener("close", () => {
		socketState = "closed";
		scheduleReconnect();
	});
	socket.addEventListener("error", () => {
		socketState = "closed";
		scheduleReconnect();
	});
}

function scheduleReconnect() {
	if (reconnectTimer !== null) {
		return;
	}
	reconnectTimer = window.setTimeout(() => {
		reconnectTimer = null;
		void refreshState();
		void refreshWorkflows();
		connectStream();
	}, 1000);
}

function stopReconnect() {
	if (reconnectTimer !== null) {
		window.clearTimeout(reconnectTimer);
		reconnectTimer = null;
	}
}

function updateScrollMode(kind: "transcript" | "workflow" | "events") {
	const node =
		kind === "transcript"
			? transcriptPane
			: kind === "workflow"
				? workflowPane
				: eventPane;
	if (!node) {
		return;
	}
	const pinned = node.scrollTop + node.clientHeight >= node.scrollHeight - 32;
	if (kind === "transcript") {
		autoScrollTranscript = pinned;
		return;
	}
	if (kind === "workflow") {
		autoScrollWorkflowEvents = pinned;
		return;
	}
	autoScrollEvents = pinned;
}

function humanizeStatus(status: string | null | undefined) {
	if (!status) {
		return "idle";
	}
	return status
		.replaceAll(/([a-z])([A-Z])/g, "$1 $2")
		.replaceAll("_", " ")
		.toLowerCase();
}

function formatClock(value: string) {
	return new Intl.DateTimeFormat("en-AU", {
		hour: "2-digit",
		minute: "2-digit",
		second: "2-digit",
	}).format(new Date(value));
}

function formatShortDateTime(value: string | null | undefined) {
	if (!value) {
		return "—";
	}
	return new Intl.DateTimeFormat("en-AU", {
		month: "short",
		day: "2-digit",
		hour: "2-digit",
		minute: "2-digit",
	}).format(new Date(value));
}

function summarizeEvent(event: RawEventRecord) {
	const payload = event.payload as {
		message?: string;
		text?: string;
		params?: {
			delta?: string;
			status?: { type?: string };
			name?: string;
		};
	};
	if (event.channel === "stderr") {
		return payload.text ?? "stderr";
	}
	if (event.channel === "lifecycle") {
		return payload.message ?? "lifecycle update";
	}
	if (event.method === "item/agentMessage/delta") {
		return payload.params?.delta ?? "message delta";
	}
	if (event.method === "thread/status/changed") {
		return payload.params?.status?.type ?? "status changed";
	}
	if (event.method === "mcpServer/startupStatus/updated") {
		return payload.params?.name ?? "mcp status updated";
	}
	return event.message_type;
}

function deltaGroupKey(event: RawEventRecord) {
	if (!event.method?.endsWith("/delta")) {
		return null;
	}
	const payload = event.payload as {
		params?: {
			itemId?: string;
			threadId?: string;
			turnId?: string;
			commandId?: string;
		};
	};
	const params = payload.params;
	if (!params) {
		return event.method;
	}
	return [
		event.method,
		params.threadId ?? "",
		params.turnId ?? "",
		params.itemId ?? "",
		params.commandId ?? "",
	].join(":");
}

function coalesceEventStream(events: RawEventRecord[]): EventStreamEntry[] {
	const entries: EventStreamEntry[] = [];
	for (const event of events) {
		const summary = summarizeEvent(event);
		const groupKey = deltaGroupKey(event);
		const lastEntry = entries.at(-1);
		if (groupKey && lastEntry?.id === groupKey) {
			lastEntry.summary += summary;
			lastEntry.chunkCount += 1;
			lastEntry.recordedAt = event.recorded_at;
			continue;
		}
		entries.push({
			id: groupKey ?? event.event_id,
			recordedAt: event.recorded_at,
			method: event.method,
			messageType: event.message_type,
			summary,
			chunkCount: 1,
		});
	}
	return entries;
}

function isImportantEvent(event: RawEventRecord) {
	if (event.channel === "stderr" || event.channel === "lifecycle") {
		return true;
	}
	if (event.message_type === "server_request") {
		return true;
	}
	if (event.method === "error" || event.method === "serverRequest/resolved") {
		return true;
	}
	if (
		event.method?.startsWith("thread/") ||
		event.method?.startsWith("turn/") ||
		event.method?.startsWith("item/started") ||
		event.method?.startsWith("item/completed")
	) {
		return true;
	}
	if (
		event.method === "item/commandExecution/terminalInteraction" ||
		event.method === "item/fileChange/outputDelta" ||
		event.method === "item/commandExecution/outputDelta" ||
		event.method === "mcpServer/startupStatus/updated" ||
		event.method === "account/rateLimits/updated"
	) {
		return true;
	}
	return false;
}

function rawEventStream(events: RawEventRecord[]): EventStreamEntry[] {
	return events.map((event) => ({
		id: event.event_id,
		recordedAt: event.recorded_at,
		method: event.method,
		messageType: event.message_type,
		summary: summarizeEvent(event),
		chunkCount: 1,
	}));
}

function eventStreamEntries() {
	if (eventStreamMode === "raw") {
		return rawEventStream(viewedRecentEvents());
	}
	if (eventStreamMode === "important") {
		return coalesceEventStream(viewedRecentEvents().filter(isImportantEvent));
	}
	return coalesceEventStream(viewedRecentEvents());
}

function summarizeWorkflowEvent(event: WorkflowEventRecord) {
	if (typeof event.payload === "object" && event.payload !== null) {
		const payload = event.payload as Record<string, unknown>;
		if (typeof payload.note === "string") {
			return payload.note;
		}
		if (typeof payload.targetDir === "string") {
			return payload.targetDir;
		}
		if (typeof payload.turnId === "string") {
			return payload.turnId;
		}
		if (typeof payload.workflowId === "string") {
			return payload.workflowId;
		}
	}
	return event.message;
}

function trimMiddle(value: string | null | undefined, left = 30, right = 16) {
	if (!value) {
		return "—";
	}
	if (value.length <= left + right + 1) {
		return value;
	}
	return `${value.slice(0, left)}…${value.slice(-right)}`;
}

function toErrorMessage(error: unknown) {
	if (error instanceof Error) {
		return error.message;
	}
	return String(error);
}

function backendOnline() {
	return dashboardState?.connection.backend_online ?? false;
}

function codexConnected() {
	return dashboardState?.connection.codex_connected ?? false;
}

function workflowActive() {
	const status = liveRun()?.status;
	return status === "starting" || status === "running" || status === "paused";
}

function workflowPaused() {
	return liveRun()?.status === "paused";
}

function pendingRequestParams(
	request = livePendingRequest(),
): Record<string, unknown> | null {
	const params = request?.params;
	if (!params || typeof params !== "object") {
		return null;
	}
	return params;
}

function pendingRequestMethodLabel(method: string | null | undefined) {
	switch (method) {
		case "item/commandExecution/requestApproval":
			return "Command approval";
		case "item/fileChange/requestApproval":
			return "File-change approval";
		case "item/permissions/requestApproval":
			return "Permission grant";
		case "item/tool/requestUserInput":
			return "User input requested";
		case "mcpServer/elicitation/request":
			return "MCP elicitation";
		case "execCommandApproval":
			return "Legacy command approval";
		case "applyPatchApproval":
			return "Legacy patch approval";
		default:
			return method ?? "Pending request";
	}
}

function pendingRequestReason(request = livePendingRequest()) {
	const reason = pendingRequestParams(request)?.reason;
	return typeof reason === "string" ? reason : null;
}

function pendingRequestCommand(request = livePendingRequest()) {
	const command = pendingRequestParams(request)?.command;
	if (typeof command === "string") {
		return command;
	}
	if (Array.isArray(command)) {
		return command
			.filter((entry): entry is string => typeof entry === "string")
			.join(" ");
	}
	return null;
}

function pendingRequestCwd(request = livePendingRequest()) {
	const cwd = pendingRequestParams(request)?.cwd;
	return typeof cwd === "string" ? cwd : null;
}

function pendingRequestGrantRoot(request = livePendingRequest()) {
	const grantRoot = pendingRequestParams(request)?.grantRoot;
	return typeof grantRoot === "string" ? grantRoot : null;
}

function pendingRequestPermissions(request = livePendingRequest()) {
	return pendingRequestParams(request)?.permissions ?? null;
}

function pendingRequestUrl(request = livePendingRequest()) {
	const url = pendingRequestParams(request)?.url;
	return typeof url === "string" ? url : null;
}

function pendingRequestQuestions(
	request = livePendingRequest(),
): PendingUserInputQuestion[] {
	const questions = pendingRequestParams(request)?.questions;
	if (!Array.isArray(questions)) {
		return [];
	}
	const normalized: PendingUserInputQuestion[] = [];
	for (const entry of questions) {
		if (!entry || typeof entry !== "object") {
			continue;
		}
		const question = entry as Record<string, unknown>;
		if (
			typeof question.id !== "string" ||
			typeof question.header !== "string" ||
			typeof question.question !== "string"
		) {
			continue;
		}
		const options = Array.isArray(question.options)
			? question.options
					.filter(
						(option): option is Record<string, unknown> =>
							Boolean(option) && typeof option === "object",
					)
					.map((option) => ({
						label: typeof option.label === "string" ? option.label : "",
						description:
							typeof option.description === "string" ? option.description : "",
					}))
					.filter((option) => option.label)
			: null;
		normalized.push({
			header: question.header,
			id: question.id,
			question: question.question,
			options,
			isOther: question.isOther === true,
			isSecret: question.isSecret === true,
		});
	}
	return normalized;
}

function stringifyJson(value: unknown) {
	return JSON.stringify(value ?? null, null, 2) ?? "null";
}

function commandApprovalAction(decision: string): PendingRequestAction | null {
	switch (decision) {
		case "accept":
			return { label: "Approve", result: { decision }, variant: "default" };
		case "acceptForSession":
			return {
				label: "Approve for session",
				result: { decision },
				variant: "secondary",
			};
		case "decline":
			return { label: "Decline", result: { decision }, variant: "outline" };
		case "cancel":
			return {
				label: "Cancel turn",
				result: { decision },
				variant: "destructive",
			};
		default:
			return null;
	}
}

function reviewApprovalAction(decision: string): PendingRequestAction | null {
	switch (decision) {
		case "approved":
			return { label: "Approve", result: { decision }, variant: "default" };
		case "approved_for_session":
			return {
				label: "Approve for session",
				result: { decision },
				variant: "secondary",
			};
		case "denied":
			return { label: "Deny", result: { decision }, variant: "outline" };
		case "abort":
			return { label: "Abort", result: { decision }, variant: "destructive" };
		default:
			return null;
	}
}

function pendingRequestActions(
	request = livePendingRequest(),
): PendingRequestAction[] {
	if (!request) {
		return [];
	}
	const params = pendingRequestParams(request);
	if (request.method === "item/commandExecution/requestApproval") {
		const available = Array.isArray(params?.availableDecisions)
			? params.availableDecisions.filter(
					(decision): decision is string => typeof decision === "string",
				)
			: [];
		const decisions = available.length
			? available
			: ["accept", "acceptForSession", "decline", "cancel"];
		return decisions
			.map((decision) => commandApprovalAction(decision))
			.filter((action): action is PendingRequestAction => action !== null);
	}
	if (request.method === "item/fileChange/requestApproval") {
		return ["accept", "acceptForSession", "decline", "cancel"]
			.map((decision) => commandApprovalAction(decision))
			.filter((action): action is PendingRequestAction => action !== null);
	}
	if (
		request.method === "execCommandApproval" ||
		request.method === "applyPatchApproval"
	) {
		return ["approved", "approved_for_session", "denied", "abort"]
			.map((decision) => reviewApprovalAction(decision))
			.filter((action): action is PendingRequestAction => action !== null);
	}
	if (request.method === "item/permissions/requestApproval") {
		const permissions = pendingRequestPermissions(request) ?? {};
		return [
			{
				label: "Grant for turn",
				result: { permissions, scope: "turn" },
				variant: "default",
			},
			{
				label: "Grant for session",
				result: { permissions, scope: "session" },
				variant: "secondary",
			},
		];
	}
	if (request.method === "mcpServer/elicitation/request") {
		const actions: PendingRequestAction[] = [
			{
				label: "Decline",
				result: { action: "decline", content: null, _meta: null },
				variant: "outline",
			},
			{
				label: "Cancel",
				result: { action: "cancel", content: null, _meta: null },
				variant: "destructive",
			},
		];
		if (pendingRequestUrl(request)) {
			actions.unshift({
				label: "Accept URL",
				result: { action: "accept", content: null, _meta: null },
				variant: "default",
			});
		}
		return actions;
	}
	return [];
}

function defaultPendingRequestResponse(request = livePendingRequest()) {
	if (!request) {
		return null;
	}
	if (request.method === "item/tool/requestUserInput") {
		return { answers: {} };
	}
	return pendingRequestActions(request)[0]?.result ?? null;
}

function stoppedOnLoopBudget() {
	const run = activeRun();
	return (
		run?.status === "failed" &&
		typeof run.last_error === "string" &&
		run.last_error.startsWith("Workflow loop budget exceeded")
	);
}

function transcriptExtras(): DerivedTranscriptEntry[] {
	const run = activeRun();
	if (!run) {
		return [];
	}
	const extras: DerivedTranscriptEntry[] = [];
	if (run.last_routing_decision) {
		const expertLine = run.last_routing_decision.expert_agent_id ?? "none";
		extras.push({
			id: `routing-decision-${run.id}`,
			speaker: "Router",
			title: "Routing Decision",
			body:
				`${run.last_routing_decision.summary}\n\n` +
				`Workflow: ${run.last_routing_decision.workflow_id}\n` +
				`Builder: ${run.last_routing_decision.executor_agent_id}\n` +
				`Judge: ${run.last_routing_decision.judge_agent_id}\n` +
				`Expert: ${expertLine}`,
			tone: "muted",
		});
	}
	if (run.last_expert_assessment) {
		extras.push({
			id: `expert-assessment-${run.id}`,
			speaker: "Expert",
			title: "Assessment",
			body: run.last_expert_assessment,
			tone: "default",
		});
	}
	if (stoppedOnLoopBudget() && run.last_continuation_prompt) {
		extras.push({
			id: `judge-continuation-${run.id}`,
			speaker: "Judge",
			title: "Continuation Prompt",
			body: run.last_continuation_prompt,
			tone: "default",
		});
	}
	return extras;
}

function transcriptHasContent() {
	return (
		(viewedState()?.transcript.length ?? 0) > 0 || transcriptExtras().length > 0
	);
}

function runDisplayName(
	run:
		| {
				run_name?: string | null;
				workflow_id: string;
		  }
		| null
		| undefined,
) {
	return run?.run_name?.trim() || run?.workflow_id || "No active workflow run";
}

function selectedWorkflow(): WorkflowDefinition | null {
	return (
		workflowCatalog?.workflows.find(
			(workflow) => workflow.id === selectedWorkflowId,
		) ?? null
	);
}

$effect(() => {
	const transcriptCount =
		(viewedState()?.transcript.length ?? 0) + transcriptExtras().length;
	void transcriptCount;
	void tick().then(() => {
		if (transcriptPane && autoScrollTranscript) {
			transcriptPane.scrollTop = transcriptPane.scrollHeight;
		}
	});
});

$effect(() => {
	const workflowEventCount = viewedRecentWorkflowEvents().length;
	void workflowEventCount;
	void tick().then(() => {
		if (workflowPane && autoScrollWorkflowEvents) {
			workflowPane.scrollTop = workflowPane.scrollHeight;
		}
	});
});

$effect(() => {
	const eventCount = viewedRecentEvents().length;
	void eventCount;
	void eventStreamMode;
	void tick().then(() => {
		if (eventPane && autoScrollEvents) {
			eventPane.scrollTop = eventPane.scrollHeight;
		}
	});
});

$effect(() => {
	const pending = livePendingRequest();
	const seedKey = pending ? `${pending.request_id}:${pending.method}` : "";
	if (seedKey === pendingRequestSeedKey) {
		return;
	}
	pendingRequestSeedKey = seedKey;
	if (!pending) {
		customServerRequestResponse = "";
		userInputDrafts = {};
		return;
	}
	customServerRequestResponse = stringifyJson(
		defaultPendingRequestResponse(pending),
	);
	userInputDrafts = Object.fromEntries(
		pendingRequestQuestions(pending).map((question) => [question.id, ""]),
	);
});

onMount(() => {
	void refreshState();
	void refreshWorkflows();
	void refreshRuns();
	connectStream();
	return () => {
		stopReconnect();
		socket?.close();
	};
});
</script>

<div class="min-h-screen bg-background text-foreground">
	<header class="border-b border-border px-5 py-4">
		<div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
			<div class="flex min-w-0 flex-col gap-1">
				<div class="text-[1rem] font-medium tracking-[-0.02em]">Shmocky</div>
				<div class="min-w-0 truncate text-[0.83rem] text-muted-foreground">
					{activeRun()?.target_dir ?? viewedState()?.workspace_root ?? "/nvme/development/shmocky"}
				</div>
			</div>
			<div class="flex flex-wrap items-center gap-5 text-[0.76rem] text-muted-foreground">
				<div class="flex items-center gap-2">
					<span
						class={`inline-block size-2 rounded-full ${
							backendOnline() ? "bg-[#8ea886] animate-pulse" : "bg-[#6d645b]"
						}`}
					></span>
					<span>backend</span>
					<span class="text-foreground">{backendOnline() ? "online" : "offline"}</span>
				</div>
				<div class="flex items-center gap-2">
					<span
						class={`inline-block size-2 rounded-full ${
							codexConnected() ? "bg-[#d0be92] animate-pulse" : "bg-[#6d645b]"
						}`}
					></span>
					<span>codex</span>
					<span class="text-foreground">
						{codexConnected() ? "connected" : "disconnected"}
					</span>
				</div>
				<div class="flex items-center gap-2">
					<span>workflow</span>
					<span class="text-foreground">
						{humanizeStatus(liveRun()?.status ?? activeRun()?.status ?? (workflowCatalog?.loaded ? "idle" : "config error"))}
					</span>
				</div>
				<div class="flex items-center gap-2">
					<span>phase</span>
					<span class="text-foreground">{humanizeStatus(liveRun()?.phase ?? activeRun()?.phase)}</span>
				</div>
				<div class="flex items-center gap-2">
					<span>stream</span>
					<span class="text-foreground">{socketState}</span>
				</div>
			</div>
		</div>
	</header>

	<main class="grid h-[calc(100svh-81px)] min-h-0 md:grid-cols-[minmax(0,1.6fr)_minmax(22rem,31rem)]">
		<section class="grid min-h-0 grid-rows-[auto_minmax(0,1fr)_auto] border-b border-border md:border-r md:border-b-0">
			<div class="flex flex-wrap items-center justify-between gap-3 border-b border-border px-5 py-3">
				<div class="flex min-w-0 flex-col gap-1">
					<div class="text-[0.92rem] font-medium">Transcript</div>
					<div class="min-w-0 truncate text-[0.78rem] text-muted-foreground">
						{runDisplayName(activeRun())}
						{#if activeRun()}
							<span> · {trimMiddle(activeRun()?.id, 18, 8)}</span>
						{/if}
					</div>
				</div>
				<div class="flex flex-wrap items-center gap-2">
					<select
						bind:value={selectedRunView}
						class="h-8 rounded-md border border-border bg-background px-2 text-[0.76rem] outline-none ring-0"
						onchange={(event) => {
							void selectRunView((event.currentTarget as HTMLSelectElement).value);
						}}
					>
						<option value="live">Current view</option>
						{#each runHistory as run}
							<option value={run.id}>
								{runDisplayName(run)} · {formatShortDateTime(run.started_at)} · {humanizeStatus(run.status)}
							</option>
						{/each}
					</select>
					<Button variant="outline" size="sm" onclick={refreshState}>Refresh</Button>
					<Button
						variant="outline"
						size="sm"
						disabled={!workflowActive() || workflowPaused() || pausingRun}
						onclick={pauseRun}
					>
						{pausingRun ? "Pausing" : "Pause"}
					</Button>
					<Button
						variant="outline"
						size="sm"
						disabled={!workflowPaused() || resumingRun}
						onclick={resumeRun}
					>
						{resumingRun ? "Resuming" : "Resume"}
					</Button>
					<Button
						variant="destructive"
						size="sm"
						disabled={!workflowActive() || stoppingRun}
						onclick={stopRun}
					>
						{stoppingRun ? "Stopping" : "Stop"}
					</Button>
				</div>
			</div>

			<div
				bind:this={transcriptPane}
				class="min-h-0 overflow-y-auto"
				onscroll={() => updateScrollMode("transcript")}
			>
				{#if loading}
					<div class="px-5 py-6 text-[0.85rem] text-muted-foreground">Loading session state…</div>
				{:else if !transcriptHasContent()}
					<div class="px-5 py-6 text-[0.85rem] text-muted-foreground">
						{#if selectedRunView === "live"}
							Launch a workflow run from the right rail to start the Codex transcript.
						{:else}
							This stored run does not have any transcript items.
						{/if}
					</div>
				{:else}
					{#each viewedState()?.transcript ?? [] as item (item.item_id)}
						<div
							transition:fade={{ duration: 120 }}
							class="grid grid-cols-[4.6rem_minmax(0,1fr)] gap-4 border-b border-border px-5 py-4"
						>
							<div class="pt-0.5 text-[0.73rem] text-muted-foreground">
								{item.role === "user" ? "You" : "Codex"}
							</div>
							<div class="min-w-0">
								<div
									class={`whitespace-pre-wrap break-words text-[0.86rem] leading-6 ${
										item.role === "assistant" ? "text-foreground" : "text-[#d2d0ca]"
									}`}
								>
									{item.text || (item.status === "streaming" ? "…" : "")}
								</div>
								<div class="mt-2 text-[0.72rem] text-muted-foreground">
									{humanizeStatus(item.status)}
									{#if item.phase}
										<span> · {item.phase.replaceAll("_", " ")}</span>
									{/if}
								</div>
							</div>
						</div>
					{/each}
					{#each transcriptExtras() as entry (entry.id)}
						<div
							transition:fade={{ duration: 120 }}
							class="grid grid-cols-[4.6rem_minmax(0,1fr)] gap-4 border-b border-border px-5 py-4"
						>
							<div class="pt-0.5 text-[0.73rem] text-muted-foreground">
								{entry.speaker}
							</div>
							<div class="min-w-0">
								<div class="text-[0.72rem] text-muted-foreground">{entry.title}</div>
								<div
									class={`mt-2 whitespace-pre-wrap break-words text-[0.86rem] leading-6 ${
										entry.tone === "default" ? "text-foreground" : "text-muted-foreground"
									}`}
								>
									{entry.body}
								</div>
							</div>
						</div>
					{/each}
				{/if}
			</div>

			<div class="border-t border-border px-5 py-4">
				{#if workflowActive() || workflowPaused()}
					<div class="grid gap-3">
						<Textarea
							bind:value={steerNote}
							rows={4}
							placeholder="Queue an operator steering note for the next Codex execution step."
							class="resize-none text-[0.84rem] leading-6"
							disabled={steeringRun}
						/>
						<div class="flex flex-wrap items-center justify-between gap-3">
							<div class="text-[0.74rem] text-muted-foreground">
								{#if requestError}
									{requestError}
								{:else if liveRun()?.pause_requested}
									Pause requested; the run will pause after the current step.
								{:else if liveRun()?.pending_steering_notes.length}
									{liveRun()?.pending_steering_notes.length} steering note(s) queued.
								{:else}
									Steering applies on the next Codex execution step.
								{/if}
							</div>
							<Button
								disabled={!steerNote.trim() || steeringRun || !workflowActive()}
								onclick={queueSteer}
							>
								{steeringRun ? "Queueing" : "Queue steer"}
							</Button>
						</div>
					</div>
				{:else}
					<div class="text-[0.78rem] text-muted-foreground">
						Workflow controls live in the right rail. When a run is active, this area becomes the
						operator steering queue.
					</div>
				{/if}
			</div>
		</section>

		<aside class="grid min-h-0 grid-rows-[auto_minmax(0,1fr)]">
			<div class="border-b border-border px-5 py-3">
				<div class="text-[0.92rem] font-medium">Session</div>
				<div class="mt-3 grid gap-2 text-[0.78rem]">
					<div class="grid grid-cols-[6rem_minmax(0,1fr)] gap-3">
						<div class="text-muted-foreground">Source repo</div>
						<div class="truncate">{activeRun()?.target_dir ?? "—"}</div>
					</div>
					<div class="grid grid-cols-[6rem_minmax(0,1fr)] gap-3">
						<div class="text-muted-foreground">Workspace</div>
						<div class="truncate">{activeRun()?.execution_dir ?? viewedState()?.workspace_root ?? "—"}</div>
					</div>
					<div class="grid grid-cols-[6rem_minmax(0,1fr)] gap-3">
						<div class="text-muted-foreground">Strategy</div>
						<div class="truncate">{activeRun()?.workspace_strategy ?? "—"}</div>
					</div>
					<div class="grid grid-cols-[6rem_minmax(0,1fr)] gap-3">
						<div class="text-muted-foreground">Branch</div>
						<div class="truncate">{activeRun()?.worktree_branch ?? "—"}</div>
					</div>
					<div class="grid grid-cols-[6rem_minmax(0,1fr)] gap-3">
						<div class="text-muted-foreground">Codex model</div>
						<div class="truncate">{viewedState()?.thread?.model ?? "—"}</div>
					</div>
					<div class="grid grid-cols-[6rem_minmax(0,1fr)] gap-3">
						<div class="text-muted-foreground">Base commit</div>
						<div class="truncate">{activeRun()?.worktree_base_commit ?? "—"}</div>
					</div>
					<div class="grid grid-cols-[6rem_minmax(0,1fr)] gap-3">
						<div class="text-muted-foreground">Sandbox</div>
						<div class="truncate">{viewedState()?.thread?.sandbox_mode ?? "—"}</div>
					</div>
					<div class="grid grid-cols-[6rem_minmax(0,1fr)] gap-3">
						<div class="text-muted-foreground">Approvals</div>
						<div class="truncate">{viewedState()?.thread?.approval_policy ?? "—"}</div>
					</div>
					<div class="grid grid-cols-[6rem_minmax(0,1fr)] gap-3">
						<div class="text-muted-foreground">Loop</div>
						<div class="truncate text-foreground">
							{#if activeRun()}
								{activeRun()?.current_loop}/{activeRun()?.max_loops} · judge {activeRun()?.judge_calls}/{activeRun()?.max_judge_calls}
							{:else}
								—
							{/if}
						</div>
					</div>
					<div class="grid grid-cols-[6rem_minmax(0,1fr)] gap-3">
						<div class="text-muted-foreground">Started</div>
						<div class="truncate text-foreground">{formatShortDateTime(activeRun()?.started_at)}</div>
					</div>
					<div class="grid grid-cols-[6rem_minmax(0,1fr)] gap-3">
						<div class="text-muted-foreground">MCP</div>
						<div class="truncate">
							{Object.entries(viewedState()?.mcp_servers ?? {})
								.map(([name, status]) => `${name}:${status}`)
								.join(", ") || "—"}
						</div>
					</div>
					{#if activeRun()?.last_judge_summary}
						<div class="border-t border-border pt-2 text-[0.74rem] text-muted-foreground">
							{activeRun()?.last_judge_decision}: {activeRun()?.last_judge_summary}
						</div>
					{/if}
					{#if activeRun()?.last_error}
						<div class="border-t border-border pt-2 text-[0.74rem] text-[#c97c6b]">
							{activeRun()?.last_error}
						</div>
					{/if}
				</div>
			</div>

			<div class="grid min-h-0 grid-rows-[auto_minmax(0,1fr)] border-t border-border">
				<div class="flex flex-wrap items-end justify-between gap-4 border-b border-border px-5 py-3">
					<div class="flex items-center gap-5">
						<button
							type="button"
							class={`border-b pb-2 text-[0.84rem] transition-colors ${
								operatorRailTab === "run"
									? "border-foreground text-foreground"
									: "border-transparent text-muted-foreground hover:text-foreground"
							}`}
							onclick={() => {
								operatorRailTab = "run";
							}}
						>
							Workflow run
						{#if livePendingRequest()}
							<span class="ml-2 inline-flex rounded-full border border-[#d0be92]/30 px-2 py-0.5 text-[0.68rem] text-[#d0be92]">
								action
							</span>
						{/if}
						</button>
						<button
							type="button"
							class={`border-b pb-2 text-[0.84rem] transition-colors ${
								operatorRailTab === "activity"
									? "border-foreground text-foreground"
									: "border-transparent text-muted-foreground hover:text-foreground"
							}`}
							onclick={() => {
								operatorRailTab = "activity";
							}}
						>
							Workflow activity
						</button>
						<button
							type="button"
							class={`border-b pb-2 text-[0.84rem] transition-colors ${
								operatorRailTab === "protocol"
									? "border-foreground text-foreground"
									: "border-transparent text-muted-foreground hover:text-foreground"
							}`}
							onclick={() => {
								operatorRailTab = "protocol";
							}}
						>
							Protocol stream
						</button>
					</div>
					{#if operatorRailTab === "protocol"}
						<div class="flex items-center gap-2">
							{#each ["coalesced", "important", "raw"] as mode}
								<Button
									variant={eventStreamMode === mode ? "secondary" : "outline"}
									size="xs"
									onclick={() => {
										eventStreamMode = mode as EventStreamMode;
									}}
								>
									{mode}
								</Button>
							{/each}
						</div>
					{:else if operatorRailTab === "run"}
						<div class="text-[0.73rem] text-muted-foreground">
							Launch a workflow and respond to live Codex approval or input requests.
						</div>
					{:else}
						<div class="text-[0.73rem] text-muted-foreground">
							Phase changes, judge decisions, steering, and run exits.
						</div>
					{/if}
				</div>

				{#if operatorRailTab === "run"}
					<div class="min-h-0 overflow-y-auto px-5 py-4">
						<div class="grid gap-3">
							{#if livePendingRequest()}
								<div class="grid gap-3 rounded-lg border border-[#6b5a4d] bg-[#171513] p-4">
									<div class="flex flex-wrap items-center justify-between gap-3">
										<div>
											<div class="text-[0.72rem] uppercase tracking-[0.08em] text-[#d0be92]">
												Operator action required
											</div>
											<div class="mt-1 text-[0.9rem] text-foreground">
												{pendingRequestMethodLabel(livePendingRequest()?.method)}
											</div>
										</div>
										<div class="text-[0.72rem] text-muted-foreground">
											{trimMiddle(livePendingRequest()?.request_id, 16, 8)}
										</div>
									</div>
									{#if pendingRequestReason(livePendingRequest())}
										<div class="text-[0.78rem] leading-6 text-muted-foreground">
											{pendingRequestReason(livePendingRequest())}
										</div>
									{/if}
									{#if pendingRequestCommand(livePendingRequest())}
										<div class="grid gap-1">
											<div class="text-[0.72rem] text-muted-foreground">Command</div>
											<pre class="overflow-x-auto rounded-md border border-border bg-background/70 p-3 text-[0.75rem] leading-6 text-foreground">{pendingRequestCommand(livePendingRequest())}</pre>
										</div>
									{/if}
									{#if pendingRequestCwd(livePendingRequest())}
										<div class="text-[0.74rem] text-muted-foreground">
											cwd: {pendingRequestCwd(livePendingRequest())}
										</div>
									{/if}
									{#if pendingRequestGrantRoot(livePendingRequest())}
										<div class="text-[0.74rem] text-muted-foreground">
											grant root: {pendingRequestGrantRoot(livePendingRequest())}
										</div>
									{/if}
									{#if pendingRequestPermissions(livePendingRequest())}
										<div class="grid gap-1">
											<div class="text-[0.72rem] text-muted-foreground">Requested permissions</div>
											<pre class="overflow-x-auto rounded-md border border-border bg-background/70 p-3 text-[0.75rem] leading-6 text-foreground">{stringifyJson(pendingRequestPermissions(livePendingRequest()))}</pre>
										</div>
									{/if}
									{#if pendingRequestUrl(livePendingRequest())}
										<div class="text-[0.74rem] text-muted-foreground">
											URL: {pendingRequestUrl(livePendingRequest())}
										</div>
									{/if}
									{#if pendingRequestQuestions(livePendingRequest()).length}
										<div class="grid gap-3 border-t border-border pt-3">
											{#each pendingRequestQuestions(livePendingRequest()) as question (question.id)}
												<div class="grid gap-2 rounded-md border border-border p-3">
													<div class="text-[0.72rem] text-muted-foreground">{question.header}</div>
													<div class="text-[0.82rem] text-foreground">{question.question}</div>
													{#if question.options?.length}
														<div class="flex flex-wrap gap-2">
															{#each question.options as option}
																<button
																	type="button"
																	class={`rounded-md border px-2 py-1 text-[0.72rem] transition-colors ${(userInputDrafts[question.id] ?? "") === option.label ? "border-[#d0be92] bg-[#2a241d] text-[#f0e4c6]" : "border-border text-muted-foreground hover:text-foreground"}`}
																	onclick={() => {
																		setUserInputDraft(question.id, option.label);
																	}}
																>
																	{option.label}
																</button>
															{/each}
														</div>
													{/if}
													<input
														type={question.isSecret ? "password" : "text"}
														value={userInputDrafts[question.id] ?? ""}
														placeholder={question.isOther || !question.options?.length ? "Enter one or more answers" : "Select an option or type a custom answer"}
														class="h-10 rounded-md border border-border bg-background px-3 text-[0.82rem] outline-none"
														oninput={(event) => {
															setUserInputDraft(question.id, (event.currentTarget as HTMLInputElement).value);
														}}
													/>
													{#if question.options?.length}
														<div class="text-[0.7rem] text-muted-foreground">
															Use commas or new lines for multiple answers.
														</div>
													{/if}
												</div>
											{/each}
											<div class="flex justify-end">
												<Button disabled={resolvingServerRequest} onclick={submitPendingUserInput}>
													{resolvingServerRequest ? "Sending" : "Submit answers"}
												</Button>
											</div>
										</div>
									{/if}
									{#if pendingRequestActions(livePendingRequest()).length}
										<div class="flex flex-wrap gap-2 border-t border-border pt-3">
											{#each pendingRequestActions(livePendingRequest()) as action}
												<Button variant={action.variant} size="sm" disabled={resolvingServerRequest} onclick={() => { void resolvePendingServerRequest(action.result); }}>
													{action.label}
												</Button>
											{/each}
										</div>
									{/if}
									<details class="border-t border-border pt-3">
										<summary class="cursor-pointer text-[0.74rem] text-muted-foreground">Custom response JSON</summary>
										<div class="mt-3 grid gap-3">
											<Textarea bind:value={customServerRequestResponse} rows={8} class="resize-y text-[0.78rem] leading-6" disabled={resolvingServerRequest} />
											<div class="flex flex-wrap items-center justify-between gap-3">
												<div class="text-[0.72rem] text-muted-foreground">Send an exact result payload when the quick actions are not enough.</div>
												<Button variant="outline" disabled={resolvingServerRequest} onclick={submitCustomServerRequestResponse}>
													{resolvingServerRequest ? "Sending" : "Send custom response"}
												</Button>
											</div>
										</div>
									</details>
									<details class="border-t border-border pt-3">
										<summary class="cursor-pointer text-[0.74rem] text-muted-foreground">Raw request payload</summary>
										<pre class="mt-3 overflow-x-auto rounded-md border border-border bg-background/70 p-3 text-[0.74rem] leading-6 text-foreground">{stringifyJson(livePendingRequest()?.params)}</pre>
									</details>
									{#if requestError}
										<div class="border-t border-border pt-3 text-[0.74rem] text-[#c97c6b]">{requestError}</div>
									{/if}
								</div>
							{/if}
							<div class="grid gap-2">
								<label class="text-[0.72rem] text-muted-foreground" for="run-name">Run name</label>
								<input
									id="run-name"
									bind:value={runName}
									placeholder="workflow testing xyz"
									class="h-10 rounded-md border border-border bg-background px-3 text-[0.84rem] outline-none"
									disabled={workflowActive()}
								/>
							</div>
							<div class="grid gap-2">
								<label class="text-[0.72rem] text-muted-foreground" for="workflow-select">
									Workflow
								</label>
								<select
									id="workflow-select"
									bind:value={selectedWorkflowId}
									class="h-10 rounded-md border border-border bg-background px-3 text-[0.84rem] outline-none ring-0"
									disabled={workflowActive()}
								>
									<option value="" disabled>Select a workflow</option>
									{#each workflowCatalog?.workflows ?? [] as workflow}
										<option value={workflow.id}>{workflow.id}</option>
									{/each}
								</select>
							</div>
							<div class="grid gap-2">
								<label class="text-[0.72rem] text-muted-foreground" for="target-dir">Source repo root</label>
								<input
									id="target-dir"
									bind:value={targetDir}
									placeholder="/absolute/path/to/git-repository-root"
									class="h-10 rounded-md border border-border bg-background px-3 text-[0.84rem] outline-none"
									disabled={workflowActive()}
								/>
							</div>
							<div class="grid gap-2">
								<label class="text-[0.72rem] text-muted-foreground" for="start-prompt">Starting prompt</label>
								<Textarea
									id="start-prompt"
									bind:value={startPrompt}
									rows={5}
									placeholder="Describe the repo task you want the workflow to carry forward."
									class="resize-none text-[0.84rem] leading-6"
									disabled={workflowActive() || startingRun}
								/>
							</div>
							<div class="flex flex-wrap items-center justify-between gap-3">
								<div class="text-[0.73rem] text-muted-foreground">
									{#if workflowCatalog?.loaded}
										Config: {trimMiddle(workflowCatalog.config_path, 24, 18)}
									{:else if workflowCatalog?.error}
										{workflowCatalog.error}
									{:else}
										Loading workflow catalog…
									{/if}
								</div>
								<Button
									disabled={
										!workflowCatalog?.loaded ||
										workflowActive() ||
										!selectedWorkflowId ||
										!targetDir.trim() ||
										!startPrompt.trim() ||
										startingRun
									}
									onclick={startWorkflowRun}
								>
									{startingRun ? "Starting run" : "Start run"}
								</Button>
							</div>
							{#if selectedWorkflow()}
								<div class="grid gap-2 border-t border-border pt-3 text-[0.76rem] text-muted-foreground">
									<div class="grid grid-cols-[6rem_minmax(0,1fr)] gap-3">
										<div>Router</div>
										<div class="truncate text-foreground">{selectedWorkflow()?.router_agent ?? "—"}</div>
									</div>
									<div class="grid grid-cols-[6rem_minmax(0,1fr)] gap-3">
										<div>Builder</div>
										<div class="truncate text-foreground">{selectedWorkflow()?.executor_agent}</div>
									</div>
									<div class="grid grid-cols-[6rem_minmax(0,1fr)] gap-3">
										<div>Expert</div>
										<div class="truncate text-foreground">{selectedWorkflow()?.expert_agent ?? "—"}</div>
									</div>
									<div class="grid grid-cols-[6rem_minmax(0,1fr)] gap-3">
										<div>Judge</div>
										<div class="truncate text-foreground">{selectedWorkflow()?.judge_agent}</div>
									</div>
									<div class="grid grid-cols-[6rem_minmax(0,1fr)] gap-3">
										<div>Budgets</div>
										<div class="truncate text-foreground">
											{selectedWorkflow()?.max_loops} loops · {selectedWorkflow()?.max_judge_calls} judges · {selectedWorkflow()?.max_runtime_minutes} min
										</div>
									</div>
									<div class="border-t border-border pt-2 text-[0.72rem]">
										Shmocky creates a managed git worktree under its own `.shmocky/worktrees/`
										area, then runs Codex there. The source repo root must be an external git
										repository root, not a nested subdirectory.
									</div>
								</div>
							{/if}
						</div>
					</div>
				{:else if operatorRailTab === "activity"}
					<div
						bind:this={workflowPane}
						class="min-h-0 overflow-y-auto"
						onscroll={() => updateScrollMode("workflow")}
					>
						{#if !viewedRecentWorkflowEvents().length}
							<div class="px-5 py-6 text-[0.82rem] text-muted-foreground">
								No workflow events captured yet.
							</div>
						{:else}
							{#each viewedRecentWorkflowEvents() as event (event.event_id)}
								<div
									transition:fade={{ duration: 120 }}
									class="grid grid-cols-[5rem_minmax(0,1fr)] gap-4 border-b border-border px-5 py-3"
								>
									<div class="pt-0.5 text-[0.72rem] text-muted-foreground">
										{formatClock(event.recorded_at)}
									</div>
									<div class="min-w-0">
										<div class="truncate text-[0.77rem] text-foreground">{event.kind}</div>
										<div class="mt-1 whitespace-pre-wrap break-words text-[0.73rem] text-muted-foreground">
											{summarizeWorkflowEvent(event)}
										</div>
									</div>
								</div>
							{/each}
						{/if}
					</div>
				{:else}
					<div
						bind:this={eventPane}
						class="min-h-0 overflow-y-auto"
						onscroll={() => updateScrollMode("events")}
					>
						{#if !eventStreamEntries().length}
							<div class="px-5 py-6 text-[0.82rem] text-muted-foreground">
								No protocol events captured yet.
							</div>
						{:else}
							{#each eventStreamEntries() as event (event.id)}
								<div
									transition:fade={{ duration: 120 }}
									class="grid grid-cols-[5rem_minmax(0,1fr)] gap-4 border-b border-border px-5 py-3"
								>
									<div class="pt-0.5 text-[0.72rem] text-muted-foreground">
										{formatClock(event.recordedAt)}
									</div>
									<div class="min-w-0">
										<div class="truncate text-[0.77rem] text-foreground">
											{event.method ?? event.messageType}
											{#if event.chunkCount > 1}
												<span class="text-muted-foreground"> · {event.chunkCount} chunks</span>
											{/if}
										</div>
										<div class="mt-1 whitespace-pre-wrap break-words text-[0.73rem] text-muted-foreground">
											{event.summary}
										</div>
									</div>
								</div>
							{/each}
						{/if}
					</div>
				{/if}
			</div>
		</aside>
	</main>
</div>
