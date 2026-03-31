<script lang="ts">
import { onMount, tick } from "svelte";
import { fade } from "svelte/transition";
import { Button } from "$lib/components/ui/button";
import { Textarea } from "$lib/components/ui/textarea";
import type {
	DashboardSnapshot,
	DashboardState,
	RawEventRecord,
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

type EventStreamMode = "coalesced" | "important" | "raw";
type OperatorRailTab = "run" | "activity" | "protocol";

let dashboardState: DashboardState | null = $state(null);
let workflowCatalog: WorkflowCatalogResponse | null = $state(null);
let recentEvents: RawEventRecord[] = $state([]);
let recentWorkflowEvents: WorkflowEventRecord[] = $state([]);
let loading = $state(true);
let requestError: string | null = $state(null);
let socketState: "connecting" | "open" | "closed" = $state("connecting");
let selectedWorkflowId = $state("");
let targetDir = $state("");
let startPrompt = $state("");
let steerNote = $state("");
let startingRun = $state(false);
let pausingRun = $state(false);
let resumingRun = $state(false);
let stoppingRun = $state(false);
let steeringRun = $state(false);
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
	return dashboardState?.workflow_run ?? null;
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

async function startWorkflowRun() {
	if (!selectedWorkflowId || !targetDir.trim() || !startPrompt.trim()) {
		return;
	}
	startingRun = true;
	try {
		const snapshot = await request<DashboardSnapshot>("/api/runs", {
			method: "POST",
			body: JSON.stringify({
				workflow_id: selectedWorkflowId,
				target_dir: targetDir.trim(),
				prompt: startPrompt.trim(),
			}),
		});
		applySnapshot(snapshot);
		startPrompt = "";
		steerNote = "";
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
		return rawEventStream(recentEvents);
	}
	if (eventStreamMode === "important") {
		return coalesceEventStream(recentEvents.filter(isImportantEvent));
	}
	return coalesceEventStream(recentEvents);
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
	const status = activeRun()?.status;
	return status === "starting" || status === "running" || status === "paused";
}

function workflowPaused() {
	return activeRun()?.status === "paused";
}

function selectedWorkflow(): WorkflowDefinition | null {
	return (
		workflowCatalog?.workflows.find(
			(workflow) => workflow.id === selectedWorkflowId,
		) ?? null
	);
}

$effect(() => {
	const transcriptCount = dashboardState?.transcript.length ?? 0;
	void transcriptCount;
	void tick().then(() => {
		if (transcriptPane && autoScrollTranscript) {
			transcriptPane.scrollTop = transcriptPane.scrollHeight;
		}
	});
});

$effect(() => {
	const workflowEventCount = recentWorkflowEvents.length;
	void workflowEventCount;
	void tick().then(() => {
		if (workflowPane && autoScrollWorkflowEvents) {
			workflowPane.scrollTop = workflowPane.scrollHeight;
		}
	});
});

$effect(() => {
	const eventCount = recentEvents.length;
	void eventCount;
	void eventStreamMode;
	void tick().then(() => {
		if (eventPane && autoScrollEvents) {
			eventPane.scrollTop = eventPane.scrollHeight;
		}
	});
});

onMount(() => {
	void refreshState();
	void refreshWorkflows();
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
					{activeRun()?.target_dir ?? dashboardState?.workspace_root ?? "/nvme/development/shmocky"}
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
						{humanizeStatus(activeRun()?.status ?? (workflowCatalog?.loaded ? "idle" : "config error"))}
					</span>
				</div>
				<div class="flex items-center gap-2">
					<span>phase</span>
					<span class="text-foreground">{humanizeStatus(activeRun()?.phase)}</span>
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
						{activeRun() ? `${activeRun()?.workflow_id} · ${trimMiddle(activeRun()?.id, 18, 8)}` : "No active workflow run"}
					</div>
				</div>
				<div class="flex flex-wrap items-center gap-2">
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
				{:else if !dashboardState?.transcript.length}
					<div class="px-5 py-6 text-[0.85rem] text-muted-foreground">
						Launch a workflow run from the right rail to start the Codex transcript.
					</div>
				{:else}
					{#each dashboardState.transcript as item (item.item_id)}
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
								{:else if activeRun()?.pause_requested}
									Pause requested; the run will pause after the current step.
								{:else if activeRun()?.pending_steering_notes.length}
									{activeRun()?.pending_steering_notes.length} steering note(s) queued.
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
						<div class="text-muted-foreground">Codex model</div>
						<div class="truncate">{dashboardState?.thread?.model ?? "—"}</div>
					</div>
					<div class="grid grid-cols-[6rem_minmax(0,1fr)] gap-3">
						<div class="text-muted-foreground">Sandbox</div>
						<div class="truncate">{dashboardState?.thread?.sandbox_mode ?? "—"}</div>
					</div>
					<div class="grid grid-cols-[6rem_minmax(0,1fr)] gap-3">
						<div class="text-muted-foreground">Approvals</div>
						<div class="truncate">{dashboardState?.thread?.approval_policy ?? "—"}</div>
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
							{Object.entries(dashboardState?.mcp_servers ?? {})
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
							Launch a workflow against a target repository or workdir.
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
								<label class="text-[0.72rem] text-muted-foreground" for="target-dir">Target directory</label>
								<input
									id="target-dir"
									bind:value={targetDir}
									placeholder="/absolute/path/to/repository-or-standalone-workdir"
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
										<div>Planner</div>
										<div class="truncate text-foreground">{selectedWorkflow()?.planner_agent}</div>
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
										Use a repository root or a standalone directory outside the Shmocky repo. Nested paths inside another repo are rejected for isolation.
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
						{#if !recentWorkflowEvents.length}
							<div class="px-5 py-6 text-[0.82rem] text-muted-foreground">
								No workflow events captured yet.
							</div>
						{:else}
							{#each recentWorkflowEvents as event (event.event_id)}
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
