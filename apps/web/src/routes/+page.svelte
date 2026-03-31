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
} from "$lib/types";

let dashboardState: DashboardState | null = $state(null);
let recentEvents: RawEventRecord[] = $state([]);
let prompt = $state("");
let loading = $state(true);
let requestError: string | null = $state(null);
let socketState: "connecting" | "open" | "closed" = $state("connecting");
let sendingPrompt = $state(false);
let startingThread = $state(false);
let interrupting = $state(false);
let transcriptPane: HTMLDivElement | null = $state(null);
let eventPane: HTMLDivElement | null = $state(null);
let autoScrollTranscript = $state(true);
let autoScrollEvents = $state(true);
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

function applySnapshot(snapshot: DashboardSnapshot) {
	dashboardState = snapshot.state;
	recentEvents = snapshot.recent_events;
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

async function startThread() {
	startingThread = true;
	try {
		const snapshot = await request<DashboardSnapshot>("/api/thread/start", {
			method: "POST",
		});
		applySnapshot(snapshot);
	} catch (error) {
		requestError = toErrorMessage(error);
	} finally {
		startingThread = false;
	}
}

async function sendPrompt() {
	const trimmed = prompt.trim();
	if (!trimmed) {
		return;
	}
	sendingPrompt = true;
	try {
		const snapshot = await request<DashboardSnapshot>("/api/turns", {
			method: "POST",
			body: JSON.stringify({ prompt: trimmed }),
		});
		applySnapshot(snapshot);
		prompt = "";
	} catch (error) {
		requestError = toErrorMessage(error);
	} finally {
		sendingPrompt = false;
	}
}

async function interruptTurn() {
	interrupting = true;
	try {
		const snapshot = await request<DashboardSnapshot>("/api/turns/interrupt", {
			method: "POST",
		});
		applySnapshot(snapshot);
	} catch (error) {
		requestError = toErrorMessage(error);
	} finally {
		interrupting = false;
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
		connectStream();
	}, 1000);
}

function stopReconnect() {
	if (reconnectTimer !== null) {
		window.clearTimeout(reconnectTimer);
		reconnectTimer = null;
	}
}

function handleComposerKeydown(event: KeyboardEvent) {
	if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
		event.preventDefault();
		void sendPrompt();
	}
}

function updateScrollMode(kind: "transcript" | "events") {
	const node = kind === "transcript" ? transcriptPane : eventPane;
	if (!node) {
		return;
	}
	const pinned = node.scrollTop + node.clientHeight >= node.scrollHeight - 32;
	if (kind === "transcript") {
		autoScrollTranscript = pinned;
		return;
	}
	autoScrollEvents = pinned;
}

function humanizeStatus(status: string | null | undefined) {
	if (!status) {
		return "idle";
	}
	return status.replaceAll(/([a-z])([A-Z])/g, "$1 $2").toLowerCase();
}

function formatClock(value: string) {
	return new Intl.DateTimeFormat("en-AU", {
		hour: "2-digit",
		minute: "2-digit",
		second: "2-digit",
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

function turnRunning() {
	return Boolean(
		dashboardState?.turn &&
			!["completed", "failed"].includes(dashboardState.turn.status),
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
	const eventCount = recentEvents.length;
	void eventCount;
	void tick().then(() => {
		if (eventPane && autoScrollEvents) {
			eventPane.scrollTop = eventPane.scrollHeight;
		}
	});
});

onMount(() => {
	void refreshState();
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
					{dashboardState?.workspace_root ?? "/nvme/development/shmocky"}
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
					<span class="text-foreground">{codexConnected() ? "connected" : "starting"}</span>
				</div>
				<div class="flex items-center gap-2">
					<span>thread</span>
					<span class="text-foreground">{humanizeStatus(dashboardState?.thread?.status)}</span>
				</div>
				<div class="flex items-center gap-2">
					<span>turn</span>
					<span class="text-foreground">{humanizeStatus(dashboardState?.turn?.status)}</span>
				</div>
				<div class="flex items-center gap-2">
					<span>stream</span>
					<span class="text-foreground">{socketState}</span>
				</div>
			</div>
		</div>
	</header>

	<main class="grid h-[calc(100svh-81px)] min-h-0 md:grid-cols-[minmax(0,1.65fr)_minmax(20rem,28rem)]">
		<section class="grid min-h-0 grid-rows-[auto_minmax(0,1fr)_auto] border-b border-border md:border-r md:border-b-0">
			<div class="flex flex-wrap items-center justify-between gap-3 border-b border-border px-5 py-3">
				<div class="flex min-w-0 flex-col gap-1">
					<div class="text-[0.92rem] font-medium">Transcript</div>
					<div class="min-w-0 truncate text-[0.78rem] text-muted-foreground">
						{trimMiddle(dashboardState?.thread?.id)}
					</div>
				</div>
				<div class="flex flex-wrap items-center gap-2">
					<Button
						variant="outline"
						size="sm"
						disabled={startingThread || !codexConnected()}
						onclick={startThread}
					>
						{startingThread ? "Starting thread" : "Start thread"}
					</Button>
					<Button variant="outline" size="sm" onclick={refreshState}>Refresh</Button>
					<Button
						variant="destructive"
						size="sm"
						disabled={!turnRunning() || interrupting}
						onclick={interruptTurn}
					>
						{interrupting ? "Interrupting" : "Interrupt"}
					</Button>
				</div>
			</div>

			<div bind:this={transcriptPane} class="min-h-0 overflow-y-auto" onscroll={() => updateScrollMode('transcript')}>
				{#if loading}
					<div class="px-5 py-6 text-[0.85rem] text-muted-foreground">Loading session state…</div>
				{:else if !dashboardState?.transcript.length}
					<div class="px-5 py-6 text-[0.85rem] text-muted-foreground">
						No thread output yet. Start the workspace thread or send a prompt.
					</div>
				{:else}
					{#each dashboardState.transcript as item (item.item_id)}
						<div
							transition:fade={{ duration: 120 }}
							class="grid grid-cols-[4.6rem_minmax(0,1fr)] gap-4 border-b border-border px-5 py-4"
						>
							<div class="pt-0.5 text-[0.73rem] text-muted-foreground">
								{item.role === 'user' ? 'You' : 'Codex'}
							</div>
							<div class="min-w-0">
								<div
									class={`whitespace-pre-wrap break-words text-[0.86rem] leading-6 ${
										item.role === 'assistant' ? 'text-foreground' : 'text-[#d2d0ca]'
									}`}
								>
									{item.text || (item.status === 'streaming' ? '…' : '')}
								</div>
								<div class="mt-2 text-[0.72rem] text-muted-foreground">
									{humanizeStatus(item.status)}
									{#if item.phase}
										<span> · {item.phase.replaceAll('_', ' ')}</span>
									{/if}
								</div>
							</div>
						</div>
					{/each}
				{/if}
			</div>

			<div class="border-t border-border px-5 py-4">
				<div class="grid gap-3">
					<Textarea
						bind:value={prompt}
						rows={4}
						placeholder="Send a prompt to the active workspace thread. Ctrl+Enter submits."
						class="resize-none text-[0.84rem] leading-6"
						disabled={!codexConnected() || sendingPrompt}
						onkeydown={handleComposerKeydown}
					/>
					<div class="flex flex-wrap items-center justify-between gap-3">
						<div class="text-[0.74rem] text-muted-foreground">
							{#if requestError}
								{requestError}
							{:else if dashboardState?.pending_server_request}
								Blocked on {dashboardState.pending_server_request.method}
							{:else}
								Raw event log: {trimMiddle(dashboardState?.event_log_path, 36, 18)}
							{/if}
						</div>
						<Button
							disabled={!prompt.trim() || sendingPrompt || !codexConnected()}
							onclick={sendPrompt}
						>
							{sendingPrompt ? "Sending" : "Send prompt"}
						</Button>
					</div>
				</div>
			</div>
		</section>

		<aside class="grid min-h-0 grid-rows-[auto_minmax(0,1fr)]">
			<div class="border-b border-border px-5 py-3">
				<div class="text-[0.92rem] font-medium">Session</div>
				<div class="mt-3 grid gap-2 text-[0.78rem]">
					<div class="grid grid-cols-[5.5rem_minmax(0,1fr)] gap-3">
						<div class="text-muted-foreground">Model</div>
						<div class="truncate">{dashboardState?.thread?.model ?? "—"}</div>
					</div>
					<div class="grid grid-cols-[5.5rem_minmax(0,1fr)] gap-3">
						<div class="text-muted-foreground">Sandbox</div>
						<div class="truncate">{dashboardState?.thread?.sandbox_mode ?? "—"}</div>
					</div>
					<div class="grid grid-cols-[5.5rem_minmax(0,1fr)] gap-3">
						<div class="text-muted-foreground">Approvals</div>
						<div class="truncate">{dashboardState?.thread?.approval_policy ?? "—"}</div>
					</div>
					<div class="grid grid-cols-[5.5rem_minmax(0,1fr)] gap-3">
						<div class="text-muted-foreground">MCP</div>
						<div class="truncate">
							{Object.entries(dashboardState?.mcp_servers ?? {})
								.map(([name, status]) => `${name}:${status}`)
								.join(", ") || "—"}
						</div>
					</div>
				</div>
			</div>

			<div class="grid min-h-0 grid-rows-[auto_minmax(0,1fr)]">
				<div class="border-b border-border px-5 py-3 text-[0.92rem] font-medium">
					Event stream
				</div>
				<div bind:this={eventPane} class="min-h-0 overflow-y-auto" onscroll={() => updateScrollMode('events')}>
					{#if !recentEvents.length}
						<div class="px-5 py-6 text-[0.82rem] text-muted-foreground">
							No protocol events captured yet.
						</div>
					{:else}
						{#each recentEvents as event (event.event_id)}
							<div
								transition:fade={{ duration: 120 }}
								class="grid grid-cols-[5rem_minmax(0,1fr)] gap-4 border-b border-border px-5 py-3"
							>
								<div class="pt-0.5 text-[0.72rem] text-muted-foreground">
									{formatClock(event.recorded_at)}
								</div>
								<div class="min-w-0">
									<div class="truncate text-[0.77rem] text-foreground">
										{event.method ?? event.message_type}
									</div>
									<div class="mt-1 truncate text-[0.73rem] text-muted-foreground">
										{summarizeEvent(event)}
									</div>
								</div>
							</div>
						{/each}
					{/if}
				</div>
			</div>
		</aside>
	</main>
</div>
