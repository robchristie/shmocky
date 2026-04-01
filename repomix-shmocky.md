This file is a merged representation of the entire codebase, combined into a single document by Repomix.

# File Summary

## Purpose
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
```
apps/
  web/
    src/
      lib/
        components/
          ui/
            button/
              button.svelte
              index.ts
            textarea/
              index.ts
              textarea.svelte
        index.ts
        types.ts
        utils.ts
      routes/
        +layout.svelte
        +page.svelte
        layout.css
      app.d.ts
      app.html
    static/
      robots.txt
    components.json
    package.json
    README.md
    svelte.config.js
    tsconfig.json
    vite.config.ts
plans/
  001-browser-mirror.md
  002-oracle-agent.md
  003-workflow-supervisor.md
scripts/
  run-backend.sh
  run-frontend.sh
src/
  shmocky/
    __init__.py
    bridge.py
    event_store.py
    main.py
    models.py
    oracle_agent.py
    projection.py
    settings.py
    supervisor.py
    workflow_config.py
tests/
  test_bridge.py
  test_oracle_agent.py
  test_projection.py
  test_supervisor.py
  test_workflow_config.py
.repomixignore
AGENTS.md
biome.json
PLANS.md
pyproject.toml
README.md
shmocky.toml
```

# Files

## File: apps/web/src/lib/components/ui/button/button.svelte
````svelte
<script lang="ts" module>
import type {
	HTMLAnchorAttributes,
	HTMLButtonAttributes,
} from "svelte/elements";
import { tv, type VariantProps } from "tailwind-variants";
import { cn, type WithElementRef } from "$lib/utils.js";

export const buttonVariants = tv({
	base: "focus-visible:border-ring focus-visible:ring-ring/50 aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive dark:aria-invalid:border-destructive/50 rounded-none border border-transparent bg-clip-padding text-xs font-medium focus-visible:ring-1 active:translate-y-px aria-invalid:ring-1 [&_svg:not([class*='size-'])]:size-4 group/button inline-flex shrink-0 items-center justify-center whitespace-nowrap transition-all outline-none select-none disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0",
	variants: {
		variant: {
			default: "bg-primary text-primary-foreground [a]:hover:bg-primary/80",
			outline:
				"border-border bg-background hover:bg-muted hover:text-foreground dark:bg-input/30 dark:border-input dark:hover:bg-input/50 aria-expanded:bg-muted aria-expanded:text-foreground",
			secondary:
				"bg-secondary text-secondary-foreground hover:bg-secondary/80 aria-expanded:bg-secondary aria-expanded:text-secondary-foreground",
			ghost:
				"hover:bg-muted hover:text-foreground dark:hover:bg-muted/50 aria-expanded:bg-muted aria-expanded:text-foreground",
			destructive:
				"bg-destructive/10 hover:bg-destructive/20 focus-visible:ring-destructive/20 dark:focus-visible:ring-destructive/40 dark:bg-destructive/20 text-destructive focus-visible:border-destructive/40 dark:hover:bg-destructive/30",
			link: "text-primary underline-offset-4 hover:underline",
		},
		size: {
			default:
				"h-8 gap-1.5 px-2.5 has-data-[icon=inline-end]:pr-2 has-data-[icon=inline-start]:pl-2",
			xs: "h-6 gap-1 rounded-none px-2 text-xs has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 [&_svg:not([class*='size-'])]:size-3",
			sm: "h-7 gap-1 rounded-none px-2.5 has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 [&_svg:not([class*='size-'])]:size-3.5",
			lg: "h-9 gap-1.5 px-2.5 has-data-[icon=inline-end]:pr-3 has-data-[icon=inline-start]:pl-3",
			icon: "size-8",
			"icon-xs": "size-6 rounded-none [&_svg:not([class*='size-'])]:size-3",
			"icon-sm": "size-7 rounded-none",
			"icon-lg": "size-9",
		},
	},
	defaultVariants: {
		variant: "default",
		size: "default",
	},
});

export type ButtonVariant = VariantProps<typeof buttonVariants>["variant"];
export type ButtonSize = VariantProps<typeof buttonVariants>["size"];

export type ButtonProps = WithElementRef<HTMLButtonAttributes> &
	WithElementRef<HTMLAnchorAttributes> & {
		variant?: ButtonVariant;
		size?: ButtonSize;
	};
</script>

<script lang="ts">
	let {
		class: className,
		variant = "default",
		size = "default",
		ref = $bindable(null),
		href = undefined,
		type = "button",
		disabled,
		children,
		...restProps
	}: ButtonProps = $props();
</script>

{#if href}
	<a
		bind:this={ref}
		data-slot="button"
		class={cn(buttonVariants({ variant, size }), className)}
		href={disabled ? undefined : href}
		aria-disabled={disabled}
		role={disabled ? "link" : undefined}
		tabindex={disabled ? -1 : undefined}
		{...restProps}
	>
		{@render children?.()}
	</a>
{:else}
	<button
		bind:this={ref}
		data-slot="button"
		class={cn(buttonVariants({ variant, size }), className)}
		{type}
		{disabled}
		{...restProps}
	>
		{@render children?.()}
	</button>
{/if}
````

## File: apps/web/src/lib/components/ui/button/index.ts
````typescript
import Root, {
	type ButtonProps,
	type ButtonSize,
	type ButtonVariant,
	buttonVariants,
} from "./button.svelte";

export {
	type ButtonProps as Props,
	type ButtonProps,
	type ButtonSize,
	type ButtonVariant,
	buttonVariants,
	Root,
	//
	Root as Button,
};
````

## File: apps/web/src/lib/components/ui/textarea/index.ts
````typescript
import Root from "./textarea.svelte";

export {
	Root,
	//
	Root as Textarea,
};
````

## File: apps/web/src/lib/components/ui/textarea/textarea.svelte
````svelte
<script lang="ts">
import type { HTMLTextareaAttributes } from "svelte/elements";
import { cn, type WithElementRef, type WithoutChildren } from "$lib/utils.js";

let {
	ref = $bindable(null),
	value = $bindable(),
	class: className,
	"data-slot": dataSlot = "textarea",
	...restProps
}: WithoutChildren<WithElementRef<HTMLTextareaAttributes>> = $props();
</script>

<textarea
	bind:this={ref}
	data-slot={dataSlot}
	class={cn(
		"border-input dark:bg-input/30 focus-visible:border-ring focus-visible:ring-ring/50 aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive dark:aria-invalid:border-destructive/50 disabled:bg-input/50 dark:disabled:bg-input/80 rounded-none border bg-transparent px-2.5 py-2 text-xs transition-colors focus-visible:ring-1 aria-invalid:ring-1 md:text-xs placeholder:text-muted-foreground flex field-sizing-content min-h-16 w-full outline-none disabled:cursor-not-allowed disabled:opacity-50",
		className
	)}
	bind:value
	{...restProps}
></textarea>
````

## File: apps/web/src/lib/index.ts
````typescript
// place files you want to import through the `$lib` alias in this folder.
````

## File: apps/web/src/lib/utils.ts
````typescript
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type WithoutChild<T> = T extends { child?: any } ? Omit<T, "child"> : T;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type WithoutChildren<T> = T extends { children?: any }
	? Omit<T, "children">
	: T;
export type WithoutChildrenOrChild<T> = WithoutChildren<WithoutChild<T>>;
export type WithElementRef<T, U extends HTMLElement = HTMLElement> = T & {
	ref?: U | null;
};
````

## File: apps/web/src/routes/+layout.svelte
````svelte
<script lang="ts">
import "./layout.css";
import favicon from "$lib/assets/favicon.svg";

let { children } = $props();
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>
{@render children()}
````

## File: apps/web/src/routes/layout.css
````css
@import 'tailwindcss';
@import "tw-animate-css";
@import "@fontsource-variable/ibm-plex-sans";
@import "@fontsource-variable/jetbrains-mono";

@custom-variant dark (&:is(.dark *));

:root {
	--background: #111315;
	--foreground: #efede8;
	--card: #171a1d;
	--card-foreground: #efede8;
	--popover: #171a1d;
	--popover-foreground: #efede8;
	--primary: #e2ded5;
	--primary-foreground: #111315;
	--secondary: #1b1f22;
	--secondary-foreground: #efede8;
	--muted: #171a1d;
	--muted-foreground: #91958d;
	--accent: #252a2f;
	--accent-foreground: #efede8;
	--destructive: #c06d56;
	--border: color-mix(in srgb, #efede8 10%, transparent);
	--input: color-mix(in srgb, #efede8 14%, transparent);
	--ring: #6b7267;
	--chart-1: #c2b38f;
	--chart-2: #9ea88f;
	--chart-3: #b58567;
	--chart-4: #8c8f75;
	--chart-5: #786f60;
	--radius: 0.625rem;
	--sidebar: #15181b;
	--sidebar-foreground: #efede8;
	--sidebar-primary: #e2ded5;
	--sidebar-primary-foreground: #111315;
	--sidebar-accent: #252a2f;
	--sidebar-accent-foreground: #efede8;
	--sidebar-border: color-mix(in srgb, #efede8 10%, transparent);
	--sidebar-ring: #6b7267;
}

.dark {
	--background: #111315;
	--foreground: #efede8;
	--card: #171a1d;
	--card-foreground: #efede8;
	--popover: #171a1d;
	--popover-foreground: #efede8;
	--primary: #e2ded5;
	--primary-foreground: #111315;
	--secondary: #1b1f22;
	--secondary-foreground: #efede8;
	--muted: #171a1d;
	--muted-foreground: #91958d;
	--accent: #252a2f;
	--accent-foreground: #efede8;
	--destructive: #c06d56;
	--border: color-mix(in srgb, #efede8 10%, transparent);
	--input: color-mix(in srgb, #efede8 14%, transparent);
	--ring: #6b7267;
	--chart-1: #c2b38f;
	--chart-2: #9ea88f;
	--chart-3: #b58567;
	--chart-4: #8c8f75;
	--chart-5: #786f60;
	--sidebar: #15181b;
	--sidebar-foreground: #efede8;
	--sidebar-primary: #e2ded5;
	--sidebar-primary-foreground: #111315;
	--sidebar-accent: #252a2f;
	--sidebar-accent-foreground: #efede8;
	--sidebar-border: color-mix(in srgb, #efede8 10%, transparent);
	--sidebar-ring: #6b7267;
}

@theme inline {
	--font-sans: 'IBM Plex Sans Variable', sans-serif;
	--font-mono: 'JetBrains Mono Variable', monospace;
	--color-sidebar-ring: var(--sidebar-ring);
	--color-sidebar-border: var(--sidebar-border);
	--color-sidebar-accent-foreground: var(--sidebar-accent-foreground);
	--color-sidebar-accent: var(--sidebar-accent);
	--color-sidebar-primary-foreground: var(--sidebar-primary-foreground);
	--color-sidebar-primary: var(--sidebar-primary);
	--color-sidebar-foreground: var(--sidebar-foreground);
	--color-sidebar: var(--sidebar);
	--color-chart-5: var(--chart-5);
	--color-chart-4: var(--chart-4);
	--color-chart-3: var(--chart-3);
	--color-chart-2: var(--chart-2);
	--color-chart-1: var(--chart-1);
	--color-ring: var(--ring);
	--color-input: var(--input);
	--color-border: var(--border);
	--color-destructive: var(--destructive);
	--color-accent-foreground: var(--accent-foreground);
	--color-accent: var(--accent);
	--color-muted-foreground: var(--muted-foreground);
	--color-muted: var(--muted);
	--color-secondary-foreground: var(--secondary-foreground);
	--color-secondary: var(--secondary);
	--color-primary-foreground: var(--primary-foreground);
	--color-primary: var(--primary);
	--color-popover-foreground: var(--popover-foreground);
	--color-popover: var(--popover);
	--color-card-foreground: var(--card-foreground);
	--color-card: var(--card);
	--color-foreground: var(--foreground);
	--color-background: var(--background);
	--radius-sm: calc(var(--radius) * 0.6);
	--radius-md: calc(var(--radius) * 0.8);
	--radius-lg: var(--radius);
	--radius-xl: calc(var(--radius) * 1.4);
	--radius-2xl: calc(var(--radius) * 1.8);
	--radius-3xl: calc(var(--radius) * 2.2);
	--radius-4xl: calc(var(--radius) * 2.6);
}

@layer base {
	* {
		@apply border-border outline-ring/50;
	}
	body {
		@apply bg-background font-sans text-foreground antialiased;
	}
	html {
		color-scheme: dark;
	}
}

@custom-variant data-open {
	&:where([data-state="open"]), &:where([data-open]:not([data-open="false"])) {
		@slot;
	}
}

@custom-variant data-closed {
	&:where([data-state="closed"]), &:where([data-closed]:not([data-closed="false"])) {
		@slot;
	}
}

@custom-variant data-checked {
	&:where([data-state="checked"]), &:where([data-checked]:not([data-checked="false"])) {
		@slot;
	}
}

@custom-variant data-unchecked {
	&:where([data-state="unchecked"]), &:where([data-unchecked]:not([data-unchecked="false"])) {
		@slot;
	}
}

@custom-variant data-selected {
	&:where([data-selected]) {
		@slot;
	}
}

@custom-variant data-disabled {
	&:where([data-disabled="true"]), &:where([data-disabled]:not([data-disabled="false"])) {
		@slot;
	}
}

@custom-variant data-active {
	&:where([data-state="active"]), &:where([data-active]:not([data-active="false"])) {
		@slot;
	}
}

@custom-variant data-horizontal {
	&:where([data-orientation="horizontal"]) {
		@slot;
	}
}

@custom-variant data-vertical {
	&:where([data-orientation="vertical"]) {
		@slot;
	}
}

@utility no-scrollbar {
	-ms-overflow-style: none;
	scrollbar-width: none;
	&::-webkit-scrollbar {
		display: none;
	}
}
````

## File: apps/web/src/app.d.ts
````typescript
// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}
}

export {};
````

## File: apps/web/src/app.html
````html
<!doctype html>
<html lang="en" class="dark">
	<head>
		<meta charset="utf-8" />
		<meta name="viewport" content="width=device-width, initial-scale=1" />
		%sveltekit.head%
	</head>
	<body data-sveltekit-preload-data="hover">
		<div style="display: contents">%sveltekit.body%</div>
	</body>
</html>
````

## File: apps/web/static/robots.txt
````
# allow crawling everything by default
User-agent: *
Disallow:
````

## File: apps/web/components.json
````json
{
	"$schema": "https://shadcn-svelte.com/schema.json",
	"tailwind": {
		"css": "src/routes/layout.css",
		"baseColor": "zinc"
	},
	"aliases": {
		"components": "$lib/components",
		"utils": "$lib/utils",
		"ui": "$lib/components/ui",
		"hooks": "$lib/hooks",
		"lib": "$lib"
	},
	"typescript": true,
	"registry": "https://shadcn-svelte.com/registry",
	"style": "lyra",
	"iconLibrary": "phosphor",
	"menuColor": "default",
	"menuAccent": "subtle"
}
````

## File: apps/web/package.json
````json
{
	"name": "web",
	"private": true,
	"version": "0.0.1",
	"type": "module",
	"scripts": {
		"dev": "vite dev",
		"build": "vite build",
		"preview": "vite preview",
		"prepare": "svelte-kit sync || echo ''",
		"check": "svelte-kit sync && svelte-check --tsconfig ./tsconfig.json",
		"check:watch": "svelte-kit sync && svelte-check --tsconfig ./tsconfig.json --watch",
		"biome:check": "biome check ."
	},
	"devDependencies": {
		"@biomejs/biome": "^2.4.10",
		"@fontsource-variable/ibm-plex-sans": "^5.2.8",
		"@fontsource-variable/jetbrains-mono": "^5.2.8",
		"@sveltejs/adapter-static": "^3.0.10",
		"@sveltejs/kit": "^2.50.2",
		"@sveltejs/vite-plugin-svelte": "^6.2.4",
		"@tailwindcss/vite": "^4.1.18",
		"@types/node": "^25.5.0",
		"clsx": "^2.1.1",
		"phosphor-svelte": "^3.1.0",
		"svelte": "^5.54.0",
		"svelte-check": "^4.4.2",
		"tailwind-merge": "^3.5.0",
		"tailwind-variants": "^3.2.2",
		"tailwindcss": "^4.1.18",
		"tw-animate-css": "^1.4.0",
		"typescript": "^5.9.3",
		"vite": "^7.3.1"
	}
}
````

## File: apps/web/README.md
````markdown
# sv

Everything you need to build a Svelte project, powered by [`sv`](https://github.com/sveltejs/cli).

## Creating a project

If you're seeing this, you've probably already done this step. Congrats!

```sh
# create a new project
npx sv create my-app
```

To recreate this project with the same configuration:

```sh
# recreate this project
npx sv@0.13.0 create --template minimal --types ts --add tailwindcss="plugins:none" sveltekit-adapter="adapter:static" --install npm apps/web
```

## Developing

Once you've created a project and installed dependencies with `npm install` (or `pnpm install` or `yarn`), start a development server:

```sh
npm run dev

# or start the server and open the app in a new browser tab
npm run dev -- --open
```

## Building

To create a production version of your app:

```sh
npm run build
```

You can preview the production build with `npm run preview`.

> To deploy your app, you may need to install an [adapter](https://svelte.dev/docs/kit/adapters) for your target environment.
````

## File: apps/web/svelte.config.js
````javascript
import { relative, sep } from "node:path";
import adapter from "@sveltejs/adapter-static";

/** @type {import('@sveltejs/kit').Config} */
const config = {
	compilerOptions: {
		// defaults to rune mode for the project, execept for `node_modules`. Can be removed in svelte 6.
		runes: ({ filename }) => {
			const relativePath = relative(import.meta.dirname, filename);
			const pathSegments = relativePath.toLowerCase().split(sep);
			const isExternalLibrary = pathSegments.includes("node_modules");

			return isExternalLibrary ? undefined : true;
		},
	},
	kit: { adapter: adapter() },
};

export default config;
````

## File: apps/web/tsconfig.json
````json
{
	"extends": "./.svelte-kit/tsconfig.json",
	"compilerOptions": {
		"rewriteRelativeImportExtensions": true,
		"allowJs": true,
		"checkJs": true,
		"esModuleInterop": true,
		"forceConsistentCasingInFileNames": true,
		"resolveJsonModule": true,
		"skipLibCheck": true,
		"sourceMap": true,
		"strict": true,
		"moduleResolution": "bundler"
	}
	// Path aliases are handled by https://svelte.dev/docs/kit/configuration#alias
	// except $lib which is handled by https://svelte.dev/docs/kit/configuration#files
	//
	// To make changes to top-level options such as include and exclude, we recommend extending
	// the generated config; see https://svelte.dev/docs/kit/configuration#typescript
}
````

## File: apps/web/vite.config.ts
````typescript
import { sveltekit } from "@sveltejs/kit/vite";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

const apiTarget = process.env.SHMOCKY_API_URL ?? "http://127.0.0.1:8000";
const allowedHostsEnv = process.env.SHMOCKY_ALLOWED_HOSTS?.trim();
const allowedHosts =
	allowedHostsEnv === "*"
		? true
		: (allowedHostsEnv
				?.split(",")
				.map((host) => host.trim())
				.filter(Boolean) ?? ["localhost", "127.0.0.1"]);

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	server: {
		allowedHosts,
		proxy: {
			"/api": {
				target: apiTarget,
				changeOrigin: true,
				ws: true,
			},
		},
	},
});
````

## File: plans/001-browser-mirror.md
````markdown
# ExecPlan 001: Browser Mirror For Codex App Server

## Summary

Ship the first vertical slice of Shmocky as a thin browser wrapper around `codex app-server`.
The backend owns a single app-server subprocess, persists raw protocol traffic to local files,
derives a small in-memory session projection, and fans updates out to the browser. The web UI
shows backend and Codex connectivity, thread and turn state, a streaming transcript, and a raw
event log that mirrors the TUI's observable flow closely enough to inspect what Codex is doing.

## Scope

In scope:

- start `codex app-server` from the backend on startup
- initialize the app-server connection and expose backend and Codex health
- support starting one workspace thread and sending turns into it
- support interrupting an active turn
- persist raw inbound and outbound JSON-RPC messages before applying projections
- expose a websocket stream for UI observability
- build an operator-style Svelte 5 SPA with a status header and browser-side transcript/event log

Out of scope for this slice:

- multi-thread management beyond a single active workspace thread
- approval workflows and user-input request handling in the browser
- resume, fork, archival, and notebook/published-book projections
- auth, budgets, policy gates, or multi-user tenancy

## Architecture

Backend:

- `FastAPI` app with a lifespan-managed `CodexAppServerBridge`
- child-process bridge talks to `codex app-server` over stdio using line-delimited JSON-RPC
- `RawEventStore` appends every outbound request and inbound response/notification to a JSONL file
- `SessionProjection` keeps current connection, thread, turn, transcript, and recent errors in memory
- websocket endpoint broadcasts raw events plus the latest projection snapshot

Frontend:

- `Svelte 5` SPA in `apps/web`
- restrained operator layout: header, transcript pane, event pane, composer
- websocket client hydrates from `/api/state`, then consumes streaming updates
- initial UI uses the project's shadcn-svelte foundation without turning the surface into a card grid

## Milestones

1. Planning and protocol capture
   - create `PLANS.md`
   - create this ExecPlan
   - validate `initialize`, `thread/start`, and `turn/start` against a live `codex app-server`
2. Backend bridge
   - add Python dependencies and backend package scaffold
   - implement event store, projection, and bridge
   - add FastAPI routes and websocket stream
3. Browser mirror
   - scaffold Svelte 5 app
   - add operator layout and live event/transcript rendering
   - wire frontend dev proxy to the backend
4. Validation and docs
   - add focused tests for projection and event persistence
   - update README with run instructions and current limits

## Validation

- `uv sync --extra dev`
- `npm --prefix apps/web install`
- `uv run ruff check .`
- `uv run ty check`
- `uv run --extra dev pytest -q`
- `npm --prefix apps/web run biome:check`
- manual smoke test: start backend, open browser UI, start a thread, send a prompt, observe streamed output

## Open Questions

- Whether the first production transport should remain stdio-only or move to an internal websocket app-server listener.
- How much of the server-request surface should be supported before the next slice: approvals only, or approvals plus tool/user-input requests.
- Whether the backend should auto-create a workspace thread on startup or wait until the browser asks for one.

## Progress Notes

- 2026-03-31: Confirmed locally that `codex app-server` accepts newline-delimited JSON-RPC over stdio.
- 2026-03-31: Confirmed the minimum request flow for this slice is `initialize`, `thread/start`, `turn/start`, with streaming notifications such as `item/agentMessage/delta`, `thread/status/changed`, and `turn/completed`.
- 2026-03-31: Implemented the FastAPI bridge, file-backed raw event log, in-memory session projection, websocket fanout, and the first browser mirror UI in `apps/web`.
- 2026-03-31: Added a thread-creation lock after smoke testing exposed a race where concurrent API calls could create two workspace threads.
- 2026-03-31: Validated the shipped slice with `uv sync --extra dev`, `uv run ruff check .`, `uv run ty check`, `uv run --extra dev pytest -q`, `npm --prefix apps/web run check`, `npm --prefix apps/web run biome:check`, and a manual smoke test against a live backend on port `8011`.
````

## File: plans/002-oracle-agent.md
````markdown
# ExecPlan 002: Oracle Sidecar Agent

## Summary

Add a thin Oracle-backed sidecar agent for slow, high-value consultation work such as advice,
second opinions, and deeper analysis. The integration should remain outside the Codex rollout
critical path: a typed backend wrapper invokes the Oracle CLI against a remote signed-in browser
service, returns the final answer, and avoids introducing a second orchestration framework.

## Scope

In scope:

- typed settings for Oracle remote host, token, and execution defaults
- a backend `OracleAgent` wrapper around `npx -y @steipete/oracle`
- one-at-a-time Oracle queries with optional attached file globs
- a minimal API endpoint to submit a prompt and receive the final answer
- a live connectivity smoke test against the configured remote Oracle host
- focused tests and README updates

Out of scope:

- folding Oracle into the Codex event stream
- multi-step Oracle workflows or autonomous retries
- frontend UI beyond the existing backend surface
- streaming Oracle partial output into the browser

## Architecture

Backend:

- `AppSettings` reads Oracle config from `.env`, accepting the existing unprefixed
  `ORACLE_REMOTE_TOKEN` and a default remote host.
- `OracleAgent` builds a CLI invocation using browser engine, remote host/token,
  `--browser-model-strategy current`, and `--write-output` to capture only the final answer.
- The wrapper serializes requests with an async lock because the remote browser target is slow
  and should not be spammed in parallel.
- FastAPI exposes `POST /api/oracle/query` returning the final answer plus execution metadata.

## Milestones

1. Planning and config
   - create this ExecPlan
   - add typed settings and request/response models
2. Oracle wrapper
   - add the `OracleAgent` service
   - capture final answer via `--write-output`
   - protect the remote path with serialized execution
3. API and validation
   - expose a minimal query endpoint
   - add tests for configuration and command construction
   - run a real smoke query against the configured remote service
4. Docs
   - update README with usage and operational caveats

## Validation

- `uv run ruff check .`
- `uv run ty check`
- `uv run --extra dev pytest -q`
- manual smoke: query Oracle through the new wrapper and confirm final answer is returned

## Open Questions

- Whether Oracle should later move from CLI wrapping to `oracle-mcp consult` for a more typed integration.
- Whether the browser UI should expose Oracle prompting directly or keep it as an API-only sidecar for now.

## Progress Notes

- 2026-03-31: Oracle README confirms remote browser clients use `--remote-host/--remote-token`, support `--write-output`, and recommend `--browser-model-strategy current` to preserve the active ChatGPT model selection.
- 2026-03-31: Implemented `OracleAgent`, typed settings, and `POST /api/oracle/query` as a serialized sidecar path outside the Codex event loop.
- 2026-03-31: Live smoke initially failed because Oracle rejects URL-style `https://host:port` values for `--remote-host`; settings now normalize URL input down to `host:port`.
- 2026-03-31: Live smoke passed against the configured remote service with prompt `Reply with exactly: oracle connectivity ok`, returning `oracle connectivity ok` in about 10.6 seconds.
````

## File: scripts/run-backend.sh
````bash
#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

: "${SHMOCKY_API_HOST:=127.0.0.1}"
: "${SHMOCKY_API_PORT:=8011}"

export SHMOCKY_API_HOST
export SHMOCKY_API_PORT

uv sync --extra dev
uv run shmocky-api
````

## File: scripts/run-frontend.sh
````bash
#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

: "${SHMOCKY_FRONTEND_HOST:=0.0.0.0}"
: "${SHMOCKY_FRONTEND_PORT:=4321}"
: "${SHMOCKY_API_URL:=http://127.0.0.1:${SHMOCKY_API_PORT:-8011}}"
: "${SHMOCKY_ALLOWED_HOSTS:=*}"

export SHMOCKY_API_URL
export SHMOCKY_ALLOWED_HOSTS

npm --prefix apps/web run dev -- --host "${SHMOCKY_FRONTEND_HOST}" --port "${SHMOCKY_FRONTEND_PORT}"
````

## File: src/shmocky/__init__.py
````python
"""Shmocky backend package."""
````

## File: tests/test_bridge.py
````python
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, cast

import pytest

from shmocky.bridge import BridgeError, CodexAppServerBridge
from shmocky.settings import AppSettings


class _FakeProcess:
    def __init__(self) -> None:
        self.pid = 4321
        self.returncode: int | None = None
        self.terminated = False

    def terminate(self) -> None:
        self.terminated = True
        self.returncode = -15

    async def wait(self) -> int:
        if self.returncode is None:
            self.returncode = 0
        return self.returncode


def test_bridge_start_cleans_up_failed_initialize(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bridge = CodexAppServerBridge(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
        )
    )
    fake_process = _FakeProcess()

    async def fake_create_subprocess_exec(*args: str, **kwargs: object) -> _FakeProcess:
        return fake_process

    async def fake_read_stdout() -> None:
        await asyncio.sleep(3600)

    async def fake_read_stderr() -> None:
        await asyncio.sleep(3600)

    async def fake_call(method: str, params: dict[str, object]) -> dict[str, object]:
        raise BridgeError("initialize failed")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    monkeypatch.setattr(bridge, "_read_stdout", fake_read_stdout)
    monkeypatch.setattr(bridge, "_read_stderr", fake_read_stderr)
    monkeypatch.setattr(bridge, "_call", fake_call)

    async def exercise() -> None:
        with pytest.raises(BridgeError, match="initialize failed"):
            await bridge.start()

    asyncio.run(exercise())

    snapshot = bridge.snapshot()

    assert fake_process.terminated is True
    assert bridge._process is None
    assert bridge._reader_task is None
    assert bridge._stderr_task is None
    assert bridge._pending == {}
    assert snapshot.state.connection.codex_connected is False
    assert snapshot.state.connection.initialized is False
    assert snapshot.state.connection.last_error == "codex app-server failed during startup"


def test_bridge_call_fails_when_process_exits_mid_request(tmp_path: Path) -> None:
    bridge = CodexAppServerBridge(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
        )
    )

    class _FakeStdin:
        def write(self, data: bytes) -> None:
            return None

        async def drain(self) -> None:
            return None

    class _LiveProcess:
        def __init__(self) -> None:
            self.stdin = _FakeStdin()

    setattr(bridge, "_process", cast(Any, _LiveProcess()))

    async def fake_record_event(*args: object, **kwargs: object):
        return None

    setattr(bridge, "_record_event", fake_record_event)

    async def exercise() -> None:
        task = asyncio.create_task(bridge._call("thread/start", {}))
        await asyncio.sleep(0)
        await bridge._handle_process_exit(23)
        with pytest.raises(BridgeError, match="thread/start failed because codex app-server exited with code 23"):
            await task
        assert bridge._pending == {}

    asyncio.run(exercise())


def test_bridge_wait_for_turn_completion_fails_fast_on_process_exit(tmp_path: Path) -> None:
    bridge = CodexAppServerBridge(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
        )
    )
    bridge._projection.apply_notification(
        "turn/started",
        {"turn": {"id": "turn-1", "status": "inProgress", "error": None}},
    )
    bridge._projection.apply_response(
        "initialize",
        {"userAgent": "shmocky-test", "codexHome": "/tmp/codex"},
    )

    async def exercise() -> None:
        task = asyncio.create_task(bridge.wait_for_turn_completion("turn-1"))
        await asyncio.sleep(0)
        await bridge._handle_process_exit(23)
        with pytest.raises(BridgeError, match="Turn turn-1 could not complete because codex app-server exited with code 23"):
            await task

    asyncio.run(exercise())
````

## File: .repomixignore
````
# Add patterns to ignore here, one per line
# Example:
# *.log
# tmp/
repomix.config.json
.vscode/
*.svg
.gitignore
.npmrc
.python-version
/docs/hedgeknight.md
/docs/ideas.md
````

## File: AGENTS.md
````markdown
# AGENTS.md

This repository builds the Shmocky autonomous supervisor and control plane around Codex. It is not a workload repository. Its job is to prepare environments, run or resume or fork or steer Codex threads, capture structured events, reduce those events into durable state, enforce policy and approval gates, and expose observability through an API and dashboard.

Keep the framework minimal. Avoid agent societies, fragile orchestration graphs, and framework-defined cognitive workflows. Prefer a thin deterministic kernel, strong prompts, explicit policy, and rich observability.

## Mission

The system should let a codex coding agent keep going on a task with minimal human intervention while remaining easy to inspect and steer. The kernel should stay small:

- preflight the environment
- start, resume, fork, and steer Codex runs
- capture raw events
- reduce events into notebook and published-book projections
- evaluate progress and health
- enforce policy, budget, and approval rules

Everything else should remain outside the critical path.

## ExecPlans

When the work is more than a trivial edit, create or update an ExecPlan under `plans/` and follow `PLANS.md` from design through implementation.

Use an ExecPlan whenever the task:

- spans multiple packages or apps
- changes architecture, schemas, or event flow
- changes agent roles, prompts, policies, or approval rules
- introduces or removes a dependency, service, or storage layer
- is expected to take more than about thirty minutes
- has unknowns that should be de-risked with prototypes or spikes

Do not ask the user for "next steps" once the ExecPlan exists unless you hit an explicit approval gate or a truly blocking external dependency.

## Engineering rules

1. Prefer additive, testable changes over broad rewrites.
2. Keep interfaces explicit and typed at every process boundary.
3. Validate environment variables and external inputs at startup.
4. Avoid hidden global state.
5. Make event payloads and persisted records versionable.
6. Include timestamps, stable ids, and provenance in stored records whenever possible.
7. Do not log secrets, tokens, raw credentials, or unnecessary sensitive payloads. Redact when in doubt.
8. Treat raw agent event logs as sensitive operational data.
9. Keep failure modes observable. A blocked run should explain why it is blocked and what action would unblock it.
10. Do not introduce a database, queue, or memory system until file-backed or simple embedded storage is clearly insufficient.
11. Prefer local files and simple projections for the first implementation.
12. Use clear names. Avoid clever abstractions that save a few lines at the cost of readability.

## CI Workflow

Current CI steps:

- `uv sync --extra dev`
- `npm --prefix apps/web install`
- `uv run ruff check .`
- `uv run ty check`
- `uv run --extra dev pytest -q`
- `npm --prefix apps/web run biome:check`

## Lint And Type Checking

- `ruff` is the fast lint/import-hygiene pass.
- `ty` is enabled as a pragmatic static check against the active `uv` environment.
- `Biome` is the frontend formatter/import-order gate for `apps/web`, including Svelte files.

## Review guidelines

When reviewing or self-reviewing changes, check the following first:

- Does the change preserve the thin-kernel architecture?
- Does it keep `codex app-server` integration structured and avoid brittle shell parsing of UI text?
- Are raw events persisted before projections are derived?
- Are approval and budget gates explicit and testable?
- Are secrets and sensitive payloads protected in logs and UI?
- Is the API boundary typed and validated?
- Are docs, commands, and tests updated to match the change?

## Completion criteria

A change is not complete until all of the following are true:

- the relevant ExecPlan is updated if one was required
- code, tests, and docs agree
- the root quality gates pass
- the change is observable in the dashboard or logs when relevant
- any new assumptions, surprises, or tradeoffs are captured in the ExecPlan or durable docs

Keep this file short, practical, and current. If the repo evolves, update this guidance rather than working around stale instructions.
````

## File: biome.json
````json
{
	"files": {
		"includes": [
			"apps/web/src/**/*.ts",
			"apps/web/src/**/*.svelte",
			"apps/web/vite.config.ts",
			"apps/web/svelte.config.js"
		]
	},
	"linter": {
		"enabled": false
	},
	"formatter": {
		"indentStyle": "tab"
	}
}
````

## File: PLANS.md
````markdown
# PLANS

An ExecPlan is the working design record for any non-trivial change in this repository.
It should stay short, concrete, and current enough that someone can read the plan and
understand both the intended architecture and the current execution status.

## When to create one

Create or update an ExecPlan when the work:

- spans multiple packages or apps
- changes architecture, schemas, or event flow
- changes agent roles, prompts, policies, or approval rules
- introduces or removes a dependency, service, or storage layer
- is expected to take more than about thirty minutes
- has material unknowns that should be de-risked with spikes

## File naming

Store plans in `plans/` using a sortable prefix and a short slug, for example:

- `plans/001-browser-mirror.md`
- `plans/002-approval-gates.md`

## Required sections

Each ExecPlan should include these sections:

1. `Summary`
2. `Scope`
3. `Architecture`
4. `Milestones`
5. `Validation`
6. `Open Questions`
7. `Progress Notes`

## Execution rules

- Update the plan before major implementation shifts.
- Record the smallest shippable slice first.
- Prefer additive milestones with explicit validation steps.
- Capture surprises, constraints, and deferred work in `Open Questions` or `Progress Notes`.
- When the change is complete, leave the plan in a state that explains what shipped and what remains.
````

## File: pyproject.toml
````toml
[build-system]
requires = ["hatchling>=1.27.0"]
build-backend = "hatchling.build"

[project]
name = "shmocky"
version = "0.1.0"
description = "Thin browser wrapper around codex app-server for autonomous engineering loops"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "fastapi>=0.135.2",
    "pydantic-settings>=2.13.1",
    "uvicorn[standard]>=0.42.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=9.0.2",
    "ruff>=0.15.8",
    "ty>=0.0.26",
]

[project.scripts]
shmocky-api = "shmocky.main:main"

[dependency-groups]
dev = [
    "pytest>=9.0.2",
    "ruff>=0.15.8",
    "ty>=0.0.26",
]

[tool.hatch.build.targets.wheel]
packages = ["src/shmocky"]

[tool.pytest.ini_options]
pythonpath = ["src"]
````

## File: src/shmocky/event_store.py
````python
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
import json
from uuid import uuid4

from .models import (
    EventChannel,
    EventDirection,
    EventMessageType,
    RawEventRecord,
    WorkflowEventRecord,
)


class RawEventStore:
    """Append-only JSONL store for raw app-server traffic."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = asyncio.Lock()
        self._sequence = _load_last_sequence(path)

    async def append(
        self,
        *,
        direction: EventDirection,
        channel: EventChannel,
        message_type: EventMessageType,
        payload: object,
        method: str | None = None,
    ) -> RawEventRecord:
        async with self._lock:
            self._sequence += 1
            record = RawEventRecord(
                sequence=self._sequence,
                event_id=str(uuid4()),
                recorded_at=datetime.now(UTC),
                direction=direction,
                channel=channel,
                message_type=message_type,
                method=method,
                payload=payload,
            )
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(record.model_dump_json())
                handle.write("\n")
            return record


class WorkflowEventStore:
    """Append-only JSONL store for workflow supervisor events."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = asyncio.Lock()
        self._sequence = _load_last_sequence(path)

    async def append(
        self,
        *,
        kind: str,
        message: str,
        payload: object | None = None,
    ) -> WorkflowEventRecord:
        async with self._lock:
            self._sequence += 1
            record = WorkflowEventRecord(
                sequence=self._sequence,
                event_id=str(uuid4()),
                recorded_at=datetime.now(UTC),
                kind=kind,
                message=message,
                payload=payload,
            )
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(record.model_dump_json())
                handle.write("\n")
            return record


def _load_last_sequence(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        last_line = ""
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    last_line = line
        if not last_line:
            return 0
        payload = json.loads(last_line)
        sequence = payload.get("sequence")
        return sequence if isinstance(sequence, int) and sequence >= 0 else 0
    except Exception:
        return 0
````

## File: src/shmocky/projection.py
````python
from __future__ import annotations

from collections import OrderedDict
from datetime import UTC, datetime
from typing import Any, cast

from .models import (
    ConnectionState,
    DashboardState,
    PendingServerRequest,
    ThreadState,
    TranscriptItem,
    TurnState,
)


class SessionProjection:
    """Small in-memory view over raw app-server events."""

    def __init__(self, *, workspace_root: str, event_log_path: str) -> None:
        self._state = DashboardState(
            workspace_root=workspace_root,
            event_log_path=event_log_path,
            connection=ConnectionState(),
        )
        self._transcript = OrderedDict[str, TranscriptItem]()

    def snapshot(self) -> DashboardState:
        state = self._state.model_copy(deep=True)
        state.transcript = [item.model_copy(deep=True) for item in self._transcript.values()]
        return state

    def mark_process_started(self, pid: int) -> None:
        self._state.connection.backend_online = True
        self._state.connection.app_server_pid = pid
        self._state.connection.last_error = None

    def mark_process_stopped(self, *, error: str | None = None) -> None:
        self._state.connection.codex_connected = False
        self._state.connection.initialized = False
        self._state.connection.app_server_pid = None
        if error is not None:
            self._state.connection.last_error = error

    def apply_response(self, method: str, result: dict[str, Any] | None) -> None:
        if method == "initialize" and result is not None:
            self._state.connection.codex_connected = True
            self._state.connection.initialized = True
            self._state.connection.app_server_user_agent = result.get("userAgent")
            self._state.connection.codex_home = result.get("codexHome")
            self._state.connection.platform_family = result.get("platformFamily")
            self._state.connection.platform_os = result.get("platformOs")
            return
        if method in {"thread/start", "thread/resume"} and result is not None:
            self._update_thread(result.get("thread"), response=result)
            return
        if method == "turn/start" and result is not None:
            self._update_turn(result.get("turn"))
            return
        if method == "turn/interrupt" and self._state.turn is not None:
            self._state.turn.status = "interruptRequested"
            self._state.turn.last_event_at = datetime.now(UTC)

    def apply_notification(self, method: str, params: dict[str, Any]) -> None:
        match method:
            case "error":
                self._state.connection.last_error = params.get("message") or str(params)
            case "thread/started":
                self._update_thread(params.get("thread"))
            case "thread/status/changed":
                if self._state.thread is not None:
                    self._state.thread.status = params.get("status", {}).get("type", "unknown")
            case "turn/started":
                self._update_turn(params.get("turn"))
            case "turn/completed":
                self._update_turn(params.get("turn"))
            case "mcpServer/startupStatus/updated":
                name = params.get("name")
                status = params.get("status")
                if isinstance(name, str) and isinstance(status, str):
                    self._state.mcp_servers[name] = status
            case "account/rateLimits/updated":
                self._state.rate_limits = params.get("rateLimits")
            case "item/started":
                self._upsert_transcript_item(params.get("item"), streaming=True)
            case "item/completed":
                self._upsert_transcript_item(params.get("item"), streaming=False)
            case "item/agentMessage/delta":
                self._append_agent_delta(params)
            case "serverRequest/resolved":
                request_id = params.get("requestId", params.get("id"))
                if self._state.pending_server_request is not None:
                    if self._state.pending_server_request.request_id == str(request_id):
                        self._state.pending_server_request = None

    def seed_transcript(self, items: list[TranscriptItem]) -> None:
        self._transcript.clear()
        for item in items:
            self._transcript[item.item_id] = item.model_copy(deep=True)
        self._trim_transcript()

    def apply_server_request(
        self,
        request_id: str,
        method: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> None:
        self._state.pending_server_request = PendingServerRequest(
            request_id=request_id,
            method=method,
            params=params,
            noted_at=datetime.now(UTC),
        )

    def _update_thread(
        self,
        thread_payload: dict[str, Any] | None,
        *,
        response: dict[str, Any] | None = None,
    ) -> None:
        if not thread_payload:
            return
        previous = self._state.thread if self._state.thread and self._state.thread.id == thread_payload["id"] else None
        sandbox = response.get("sandbox") if response else None
        sandbox_type = previous.sandbox_mode if previous is not None else None
        if isinstance(sandbox, dict):
            sandbox_type = sandbox.get("type")
        self._state.thread = ThreadState(
            id=thread_payload["id"],
            status=thread_payload.get("status", {}).get("type", previous.status if previous is not None else "idle"),
            cwd=thread_payload.get("cwd", previous.cwd if previous is not None else None),
            model=response.get("model") if response else (previous.model if previous is not None else None),
            model_provider=(
                response.get("modelProvider")
                if response
                else thread_payload.get("modelProvider", previous.model_provider if previous is not None else None)
            ),
            approval_policy=(
                response.get("approvalPolicy")
                if response
                else (previous.approval_policy if previous is not None else None)
            ),
            sandbox_mode=sandbox_type,
            reasoning_effort=(
                response.get("reasoningEffort")
                if response
                else (previous.reasoning_effort if previous is not None else None)
            ),
            created_at=thread_payload.get("createdAt", previous.created_at if previous is not None else None),
            updated_at=thread_payload.get("updatedAt", previous.updated_at if previous is not None else None),
        )

    def _update_turn(self, turn_payload: dict[str, Any] | None) -> None:
        if not turn_payload:
            return
        self._state.turn = TurnState(
            id=turn_payload["id"],
            status=turn_payload.get("status", "unknown"),
            last_event_at=datetime.now(UTC),
            error=self._extract_turn_error(turn_payload.get("error")),
        )

    def _upsert_transcript_item(self, item: dict[str, Any] | None, *, streaming: bool) -> None:
        if not item:
            return
        item_type = item.get("type")
        item_id = item.get("id")
        if item_type not in {"userMessage", "agentMessage"} or not isinstance(item_id, str):
            return
        role = "user" if item_type == "userMessage" else "assistant"
        text = self._extract_item_text(item)
        phase = item.get("phase")
        turn_id = self._state.turn.id if self._state.turn is not None else None
        current = self._transcript.get(item_id)
        if current is None:
            current = TranscriptItem(
                item_id=item_id,
                role=role,
                text=text,
                phase=phase,
                status="streaming" if streaming and role == "assistant" else "completed",
                turn_id=turn_id,
            )
            self._transcript[item_id] = current
        else:
            current.text = text or current.text
            current.phase = phase or current.phase
            current.status = "streaming" if streaming and role == "assistant" else "completed"
        self._trim_transcript()

    def _append_agent_delta(self, params: dict[str, Any]) -> None:
        item_id = params.get("itemId")
        delta = params.get("delta")
        if not isinstance(item_id, str) or not isinstance(delta, str):
            return
        current = self._transcript.get(item_id)
        if current is None:
            current = TranscriptItem(
                item_id=item_id,
                role="assistant",
                text="",
                status="streaming",
                turn_id=params.get("turnId"),
            )
            self._transcript[item_id] = current
        current.text += delta
        current.status = "streaming"
        self._trim_transcript()

    def _trim_transcript(self, *, limit: int = 200) -> None:
        while len(self._transcript) > limit:
            self._transcript.popitem(last=False)

    @staticmethod
    def _extract_turn_error(error: object) -> str | None:
        if error is None:
            return None
        if isinstance(error, str):
            return error
        if isinstance(error, dict):
            message = cast(dict[str, object], error).get("message")
            if isinstance(message, str):
                return message
        return str(error)

    @staticmethod
    def _extract_item_text(item: dict[str, Any]) -> str:
        if item.get("type") == "agentMessage":
            text = item.get("text")
            return text if isinstance(text, str) else ""
        content = item.get("content")
        if not isinstance(content, list):
            return ""
        parts: list[str] = []
        for entry in content:
            if isinstance(entry, dict) and entry.get("type") == "text":
                text = entry.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "".join(parts)
````

## File: tests/test_projection.py
````python
from __future__ import annotations

from shmocky.projection import SessionProjection


def test_projection_builds_streaming_transcript() -> None:
    projection = SessionProjection(
        workspace_root="/tmp/workspace",
        event_log_path="/tmp/workspace/.shmocky/events/test.jsonl",
    )

    projection.apply_response(
        "thread/start",
        {
            "thread": {
                "id": "thread-1",
                "status": {"type": "idle"},
                "cwd": "/tmp/workspace",
                "createdAt": 1,
                "updatedAt": 1,
            },
            "model": "gpt-5.4",
            "modelProvider": "openai",
            "approvalPolicy": "never",
            "sandbox": {"type": "workspaceWrite"},
            "reasoningEffort": "high",
        },
    )
    projection.apply_notification(
        "turn/started",
        {
            "threadId": "thread-1",
            "turn": {"id": "turn-1", "status": "inProgress", "error": None},
        },
    )
    projection.apply_notification(
        "item/started",
        {
            "threadId": "thread-1",
            "turnId": "turn-1",
            "item": {
                "type": "userMessage",
                "id": "user-1",
                "content": [{"type": "text", "text": "hello"}],
            },
        },
    )
    projection.apply_notification(
        "item/started",
        {
            "threadId": "thread-1",
            "turnId": "turn-1",
            "item": {
                "type": "agentMessage",
                "id": "assistant-1",
                "text": "",
                "phase": "final_answer",
            },
        },
    )
    projection.apply_notification(
        "item/agentMessage/delta",
        {
            "threadId": "thread-1",
            "turnId": "turn-1",
            "itemId": "assistant-1",
            "delta": "hello",
        },
    )
    projection.apply_notification(
        "item/completed",
        {
            "threadId": "thread-1",
            "turnId": "turn-1",
            "item": {
                "type": "agentMessage",
                "id": "assistant-1",
                "text": "hello there",
                "phase": "final_answer",
            },
        },
    )

    snapshot = projection.snapshot()

    assert snapshot.thread is not None
    assert snapshot.thread.id == "thread-1"
    assert snapshot.turn is not None
    assert snapshot.turn.id == "turn-1"
    assert [item.role for item in snapshot.transcript] == ["user", "assistant"]
    assert snapshot.transcript[0].text == "hello"
    assert snapshot.transcript[1].text == "hello there"
    assert snapshot.transcript[1].status == "completed"


def test_projection_tracks_server_requests() -> None:
    projection = SessionProjection(
        workspace_root="/tmp/workspace",
        event_log_path="/tmp/workspace/.shmocky/events/test.jsonl",
    )

    projection.apply_server_request(
        "42",
        "item/commandExecution/requestApproval",
        params={"command": "git status", "reason": "Needs approval."},
    )
    snapshot = projection.snapshot()

    assert snapshot.pending_server_request is not None
    assert snapshot.pending_server_request.request_id == "42"
    assert snapshot.pending_server_request.method == "item/commandExecution/requestApproval"
    assert snapshot.pending_server_request.params == {
        "command": "git status",
        "reason": "Needs approval.",
    }

    projection.apply_notification(
        "serverRequest/resolved",
        {"requestId": "42", "threadId": "thread-1"},
    )

    assert projection.snapshot().pending_server_request is None


def test_thread_started_notification_preserves_response_metadata() -> None:
    projection = SessionProjection(
        workspace_root="/tmp/workspace",
        event_log_path="/tmp/workspace/.shmocky/events/test.jsonl",
    )

    projection.apply_response(
        "thread/start",
        {
            "thread": {
                "id": "thread-1",
                "status": {"type": "idle"},
                "cwd": "/tmp/workspace",
                "createdAt": 1,
                "updatedAt": 1,
                "modelProvider": "openai",
            },
            "model": "gpt-5.4",
            "modelProvider": "openai",
            "approvalPolicy": "never",
            "sandbox": {"type": "workspaceWrite"},
            "reasoningEffort": "high",
        },
    )

    projection.apply_notification(
        "thread/started",
        {
            "thread": {
                "id": "thread-1",
                "status": {"type": "idle"},
                "cwd": "/tmp/workspace",
                "createdAt": 1,
                "updatedAt": 2,
                "modelProvider": "openai",
            },
        },
    )

    snapshot = projection.snapshot()

    assert snapshot.thread is not None
    assert snapshot.thread.model == "gpt-5.4"
    assert snapshot.thread.approval_policy == "never"
    assert snapshot.thread.sandbox_mode == "workspaceWrite"
    assert snapshot.thread.reasoning_effort == "high"
    assert snapshot.thread.updated_at == 2
````

## File: src/shmocky/bridge.py
````python
from __future__ import annotations

import asyncio
import contextlib
import json
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .event_store import RawEventStore
from .models import (
    CodexAgentConfig,
    DashboardSnapshot,
    EventChannel,
    EventDirection,
    EventMessageType,
    RawEventRecord,
    TranscriptItem,
    StreamEnvelope,
)
from .projection import SessionProjection
from .settings import AppSettings


class BridgeError(RuntimeError):
    """Raised when the app-server bridge cannot complete a request."""


class CodexAppServerBridge:
    def __init__(
        self,
        settings: AppSettings,
        *,
        workspace_root: Path | None = None,
        event_log_dir: Path | None = None,
        agent_config: CodexAgentConfig | None = None,
    ) -> None:
        self._settings = settings
        self._workspace_root = (workspace_root or settings.workspace_root).expanduser().resolve()
        self._agent_config = agent_config or CodexAgentConfig(role="engineer")
        event_log_root = event_log_dir or settings.event_log_dir
        event_log_path = self._make_event_log_path(event_log_root)
        self._event_store = RawEventStore(event_log_path)
        self._projection = SessionProjection(
            workspace_root=str(self._workspace_root),
            event_log_path=str(event_log_path),
        )
        self._recent_events: deque[RawEventRecord] = deque(maxlen=300)
        self._process: asyncio.subprocess.Process | None = None
        self._reader_task: asyncio.Task[None] | None = None
        self._stderr_task: asyncio.Task[None] | None = None
        self._send_lock = asyncio.Lock()
        self._thread_lock = asyncio.Lock()
        self._subscribers: set[asyncio.Queue[StreamEnvelope]] = set()
        self._request_counter = 0
        self._pending: dict[str, tuple[str, asyncio.Future[dict[str, Any]]]] = {}

    async def start(self) -> None:
        self._settings.event_log_dir.mkdir(parents=True, exist_ok=True)
        try:
            self._process = await asyncio.create_subprocess_exec(
                self._settings.codex_command,
                "app-server",
                cwd=str(self._workspace_root),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            self._projection.mark_process_started(self._process.pid)
            await self._append_internal_event(
                message="codex app-server started",
                payload={"pid": self._process.pid},
            )
            self._reader_task = asyncio.create_task(self._read_stdout())
            self._stderr_task = asyncio.create_task(self._read_stderr())
            await self._call(
                "initialize",
                {
                    "clientInfo": {
                        "name": "shmocky",
                        "title": "Shmocky Browser Mirror",
                        "version": "0.1.0",
                    },
                    "capabilities": {
                        "experimentalApi": self._settings.experimental_api,
                    },
                },
            )
        except Exception:
            await self._cleanup_failed_start()
            raise

    async def _cleanup_failed_start(self) -> None:
        for request_id, (_, future) in list(self._pending.items()):
            if not future.done():
                future.cancel()
            self._pending.pop(request_id, None)
        if self._reader_task is not None:
            self._reader_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._reader_task
            self._reader_task = None
        if self._stderr_task is not None:
            self._stderr_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._stderr_task
            self._stderr_task = None
        if self._process is not None and self._process.returncode is None:
            self._process.terminate()
            with contextlib.suppress(ProcessLookupError, TimeoutError):
                await asyncio.wait_for(self._process.wait(), timeout=5)
        self._projection.mark_process_stopped(error="codex app-server failed during startup")
        self._process = None

    async def stop(self) -> None:
        if self._process is None:
            return
        if self._process.returncode is None:
            self._process.terminate()
            with contextlib.suppress(ProcessLookupError):
                await asyncio.wait_for(self._process.wait(), timeout=5)
        for task in (self._reader_task, self._stderr_task):
            if task is not None:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
        self._projection.mark_process_stopped()
        await self._append_internal_event(message="codex app-server stopped")
        self._process = None

    def snapshot(self) -> DashboardSnapshot:
        return DashboardSnapshot(
            state=self._projection.snapshot(),
            recent_events=[event.model_copy(deep=True) for event in self._recent_events],
        )

    async def resume_thread(self, thread_id: str) -> DashboardSnapshot:
        async with self._thread_lock:
            state = self._projection.snapshot()
            if state.thread is None or state.thread.id != thread_id:
                config: dict[str, Any] = {}
                if self._agent_config.reasoning_effort is not None:
                    config["model_reasoning_effort"] = self._agent_config.reasoning_effort
                if self._agent_config.web_access is not None:
                    config["web_search"] = self._agent_config.web_access
                await self._call(
                    "thread/resume",
                    {
                        "threadId": thread_id,
                        "cwd": str(self._workspace_root),
                        "approvalPolicy": self._agent_config.approval_policy,
                        "sandbox": self._agent_config.sandbox_mode,
                        "developerInstructions": self._agent_config.startup_prompt,
                        "model": self._agent_config.model,
                        "modelProvider": self._agent_config.model_provider,
                        "serviceTier": self._agent_config.service_tier,
                        "config": config or None,
                    },
                )
        return self.snapshot()

    def seed_transcript(self, items: list[TranscriptItem]) -> DashboardSnapshot:
        self._projection.seed_transcript(items)
        return self.snapshot()

    async def ensure_thread(self) -> DashboardSnapshot:
        async with self._thread_lock:
            state = self._projection.snapshot()
            if state.thread is None:
                config: dict[str, Any] = {}
                if self._agent_config.reasoning_effort is not None:
                    config["model_reasoning_effort"] = self._agent_config.reasoning_effort
                if self._agent_config.web_access is not None:
                    config["web_search"] = self._agent_config.web_access
                await self._call(
                    "thread/start",
                    {
                        "cwd": str(self._workspace_root),
                        "approvalPolicy": self._agent_config.approval_policy,
                        "sandbox": self._agent_config.sandbox_mode,
                        "developerInstructions": self._agent_config.startup_prompt,
                        "model": self._agent_config.model,
                        "modelProvider": self._agent_config.model_provider,
                        "serviceTier": self._agent_config.service_tier,
                        "config": config or None,
                        "experimentalRawEvents": False,
                        "persistExtendedHistory": True,
                    },
                )
        return self.snapshot()

    async def start_turn(self, prompt: str) -> DashboardSnapshot:
        state = await self.ensure_thread()
        thread = state.state.thread
        if thread is None:
            raise BridgeError("Thread could not be created")
        await self._call(
            "turn/start",
            {
                "threadId": thread.id,
                "input": [
                    {
                        "type": "text",
                        "text": prompt,
                    }
                ],
            },
        )
        return self.snapshot()

    async def interrupt_turn(self) -> DashboardSnapshot:
        state = self._projection.snapshot()
        if state.thread is None or state.turn is None:
            return self.snapshot()
        await self._call(
            "turn/interrupt",
            {
                "threadId": state.thread.id,
                "turnId": state.turn.id,
            },
        )
        return self.snapshot()

    async def resolve_server_request(self, request_id: str, *, result: Any) -> DashboardSnapshot:
        state = self._projection.snapshot()
        pending = state.pending_server_request
        if pending is None:
            raise BridgeError("There is no pending server request to resolve.")
        if pending.request_id != request_id:
            raise BridgeError(
                f"Pending server request is '{pending.request_id}', not '{request_id}'."
            )
        await self._send_message(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result,
            },
            direction="outbound",
            channel="rpc",
            message_type="response",
        )
        return self.snapshot()

    async def wait_for_turn_completion(self, turn_id: str) -> DashboardSnapshot:
        queue = await self.subscribe()
        try:
            while True:
                snapshot = self.snapshot()
                self._raise_if_turn_unavailable(snapshot, turn_id)
                if self._is_terminal_turn(snapshot, turn_id):
                    return snapshot
                envelope = await queue.get()
                envelope_snapshot = DashboardSnapshot(
                    state=envelope.state,
                    recent_events=[],
                )
                self._raise_if_turn_unavailable(envelope_snapshot, turn_id)
                if self._is_terminal_turn(envelope_snapshot, turn_id):
                    return self.snapshot()
        finally:
            self.unsubscribe(queue)

    async def subscribe(self) -> asyncio.Queue[StreamEnvelope]:
        queue: asyncio.Queue[StreamEnvelope] = asyncio.Queue(maxsize=512)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[StreamEnvelope]) -> None:
        self._subscribers.discard(queue)

    async def _call(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if self._process is None or self._process.stdin is None:
            raise BridgeError("codex app-server is not running")
        self._request_counter += 1
        request_id = str(self._request_counter)
        message = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }
        loop = asyncio.get_running_loop()
        future: asyncio.Future[dict[str, Any]] = loop.create_future()
        self._pending[request_id] = (method, future)
        await self._send_message(
            message,
            direction="outbound",
            channel="rpc",
            message_type="request",
            method=method,
        )
        try:
            response = await asyncio.wait_for(
                future,
                timeout=self._settings.request_timeout_seconds,
            )
        except TimeoutError as exc:
            self._pending.pop(request_id, None)
            raise BridgeError(f"Timed out waiting for {method}") from exc
        if "error" in response:
            raise BridgeError(f"{method} failed: {response['error']}")
        return response.get("result", {})

    async def _read_stdout(self) -> None:
        assert self._process is not None
        assert self._process.stdout is not None
        while True:
            line = await self._process.stdout.readline()
            if not line:
                return_code = await self._process.wait()
                await self._handle_process_exit(return_code)
                return
            raw = line.decode("utf-8").strip()
            if not raw:
                continue
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                await self._append_internal_event(
                    message="received invalid JSON from app-server",
                    payload={"raw": raw},
                )
                continue
            await self._handle_inbound_message(message)

    async def _handle_process_exit(self, return_code: int) -> None:
        error = f"codex app-server exited with code {return_code}"
        self._projection.mark_process_stopped(error=error)
        self._fail_pending_calls(error)
        await self._append_internal_event(
            message="codex app-server exited",
            payload={"returncode": return_code},
        )

    def _fail_pending_calls(self, message: str) -> None:
        for request_id, (method, future) in list(self._pending.items()):
            if not future.done():
                future.set_exception(
                    BridgeError(f"{method} failed because {message}.")
                )
            self._pending.pop(request_id, None)

    async def _read_stderr(self) -> None:
        assert self._process is not None
        assert self._process.stderr is not None
        while True:
            line = await self._process.stderr.readline()
            if not line:
                return
            text = line.decode("utf-8").rstrip()
            if not text:
                continue
            await self._record_event(
                {"text": text},
                direction="inbound",
                channel="stderr",
                message_type="stderr",
            )

    async def _handle_inbound_message(self, message: dict[str, Any]) -> None:
        message_type = self._classify_inbound_message(message)
        record = await self._record_event(
            message,
            direction="inbound",
            channel="rpc",
            message_type=message_type,
            method=message.get("method"),
        )
        if message_type == "response":
            request_id = str(message.get("id"))
            pending = self._pending.pop(request_id, None)
            if pending is not None:
                method, future = pending
                if "result" in message and isinstance(message["result"], dict):
                    self._projection.apply_response(method, message["result"])
                if not future.done():
                    future.set_result(message)
        elif message_type == "notification":
            method = message.get("method")
            params = message.get("params")
            if isinstance(method, str) and isinstance(params, dict):
                self._projection.apply_notification(method, params)
        elif message_type == "server_request":
            request_id = str(message.get("id"))
            method = str(message.get("method"))
            params = message.get("params")
            self._projection.apply_server_request(
                request_id=request_id,
                method=method,
                params=params if isinstance(params, dict) else None,
            )
        await self._broadcast_event(record)

    async def _send_message(
        self,
        message: dict[str, Any],
        *,
        direction: EventDirection,
        channel: EventChannel,
        message_type: EventMessageType,
        method: str | None = None,
    ) -> None:
        if self._process is None or self._process.stdin is None:
            raise BridgeError("codex app-server is not running")
        await self._record_event(
            message,
            direction=direction,
            channel=channel,
            message_type=message_type,
            method=method,
        )
        encoded = json.dumps(message, separators=(",", ":")) + "\n"
        async with self._send_lock:
            self._process.stdin.write(encoded.encode("utf-8"))
            await self._process.stdin.drain()

    async def _record_event(
        self,
        payload: object,
        *,
        direction: EventDirection,
        channel: EventChannel,
        message_type: EventMessageType,
        method: str | None = None,
    ) -> RawEventRecord:
        record = await self._event_store.append(
            direction=direction,
            channel=channel,
            message_type=message_type,
            payload=payload,
            method=method,
        )
        self._recent_events.append(record)
        return record

    async def _append_internal_event(
        self,
        *,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        record = await self._record_event(
            {
                "message": message,
                "payload": payload or {},
                "recordedAt": datetime.now(UTC).isoformat(),
            },
            direction="internal",
            channel="lifecycle",
            message_type="lifecycle",
        )
        await self._broadcast_event(record)

    async def _broadcast_event(self, record: RawEventRecord) -> None:
        if not self._subscribers:
            return
        envelope = StreamEnvelope(type="event", event=record, state=self._projection.snapshot())
        stale: list[asyncio.Queue[StreamEnvelope]] = []
        for queue in self._subscribers:
            try:
                queue.put_nowait(envelope)
            except asyncio.QueueFull:
                stale.append(queue)
        for queue in stale:
            self._subscribers.discard(queue)

    @staticmethod
    def _classify_inbound_message(message: dict[str, Any]) -> EventMessageType:
        if "id" in message and "method" in message:
            return "server_request"
        if "id" in message:
            return "response"
        if "method" in message:
            return "notification"
        return "unknown"

    @staticmethod
    def _make_event_log_path(directory: Path) -> Path:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        return directory / f"codex-app-server-{timestamp}.jsonl"

    @staticmethod
    def _is_terminal_turn(snapshot: DashboardSnapshot, turn_id: str) -> bool:
        turn = snapshot.state.turn
        if turn is None or turn.id != turn_id:
            return False
        return turn.status in {"completed", "failed", "cancelled", "interrupted"}

    @staticmethod
    def _raise_if_turn_unavailable(snapshot: DashboardSnapshot, turn_id: str) -> None:
        turn = snapshot.state.turn
        if turn is None or turn.id != turn_id:
            return
        if turn.status in {"completed", "failed", "cancelled", "interrupted"}:
            return
        connection = snapshot.state.connection
        if connection.codex_connected:
            return
        if connection.last_error:
            raise BridgeError(
                f"Turn {turn_id} could not complete because {connection.last_error}."
            )
        raise BridgeError(
            f"Turn {turn_id} could not complete because the codex app-server is unavailable."
        )
````

## File: src/shmocky/workflow_config.py
````python
from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .models import AgentDefinition, WorkflowCatalogResponse, WorkflowDefinition
from .settings import AppSettings

DEFAULT_PLAN_PROMPT_TEMPLATE = """You are preparing the first execution plan for this workflow run.

Goal:
{goal}

Produce a concrete implementation plan for the repository in front of you. Keep it actionable and
focused on the next small slice that should actually be executed now."""

DEFAULT_EXECUTE_PROMPT_TEMPLATE = """Execute the next slice of work for this workflow run.

Goal:
{goal}

Plan:
{plan}

Carry the work forward in the repository. If you are blocked, say exactly what blocked you."""

DEFAULT_EXPERT_PROMPT_TEMPLATE = """You are the workflow expert advisor. Review the run context below
and return plain text only.

Your job:
- assess the current run state and the latest Codex work
- identify the most important risks, missed opportunities, or next experiments
- suggest what the judge should consider before deciding whether to continue

Keep the response concise but specific. Free text is fine.

Context:
{judge_bundle}"""

DEFAULT_JUDGE_PROMPT_TEMPLATE = """You are the workflow judge. Review the run context below and
return plain text only in this exact labeled format:

Decision: continue | complete | fail
Summary: short operator-facing summary
Next prompt:
required only when Decision is continue; plain text, may be multiline
Completion note:
optional only when Decision is complete
Failure reason:
optional only when Decision is fail

Rules:
- Return plain text only.
- Choose "continue" only when a single next Codex prompt would materially advance the goal.
- Choose "complete" only when the goal appears satisfied.
- Choose "fail" only when the run is blocked or the approach is no longer viable.
- If you choose "continue", write a complete next Codex prompt under "Next prompt:".

Context:
{judge_bundle}"""


class WorkflowConfigError(RuntimeError):
    pass


class WorkflowConfigLoader:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    @property
    def path(self) -> Path:
        return self._settings.workflow_config_path

    def load(self) -> WorkflowCatalogResponse:
        path = self.path
        if not path.exists():
            raise WorkflowConfigError(f"Workflow config file not found: {path}")

        try:
            with path.open("rb") as handle:
                payload = tomllib.load(handle)
        except tomllib.TOMLDecodeError as exc:
            raise WorkflowConfigError(f"Invalid TOML in {path}: {exc}") from exc

        agents = self._load_agents(payload.get("agents"))
        workflows = self._load_workflows(payload.get("workflows"), agents)
        return WorkflowCatalogResponse(
            config_path=str(path),
            loaded=True,
            agents=agents,
            workflows=workflows,
        )

    def _load_agents(self, payload: object) -> list[AgentDefinition]:
        if not isinstance(payload, dict):
            raise WorkflowConfigError("Workflow config must define an [agents] table.")
        agents: list[AgentDefinition] = []
        for agent_id, raw_agent in payload.items():
            if not isinstance(agent_id, str) or not isinstance(raw_agent, dict):
                raise WorkflowConfigError("Each agent entry must be a TOML table.")
            normalized_agent = dict(raw_agent)
            try:
                agent = AgentDefinition.model_validate({"id": agent_id, **normalized_agent})
            except ValidationError as exc:
                raise WorkflowConfigError(f"Invalid agent '{agent_id}': {exc}") from exc
            self._validate_agent(agent, normalized_agent)
            agents.append(agent)
        if not agents:
            raise WorkflowConfigError("Workflow config must define at least one agent.")
        return sorted(agents, key=lambda agent: agent.id)

    def _load_workflows(
        self,
        payload: object,
        agents: list[AgentDefinition],
    ) -> list[WorkflowDefinition]:
        if not isinstance(payload, dict):
            raise WorkflowConfigError("Workflow config must define a [workflows] table.")
        agent_by_id = {agent.id: agent for agent in agents}
        workflows: list[WorkflowDefinition] = []
        for workflow_id, raw_workflow in payload.items():
            if not isinstance(workflow_id, str) or not isinstance(raw_workflow, dict):
                raise WorkflowConfigError("Each workflow entry must be a TOML table.")
            workflow_payload = {
                "id": workflow_id,
                "plan_prompt_template": DEFAULT_PLAN_PROMPT_TEMPLATE,
                "execute_prompt_template": DEFAULT_EXECUTE_PROMPT_TEMPLATE,
                "expert_prompt_template": DEFAULT_EXPERT_PROMPT_TEMPLATE,
                "judge_prompt_template": DEFAULT_JUDGE_PROMPT_TEMPLATE,
                **raw_workflow,
            }
            try:
                workflow = WorkflowDefinition.model_validate(workflow_payload)
            except ValidationError as exc:
                raise WorkflowConfigError(f"Invalid workflow '{workflow_id}': {exc}") from exc
            for ref_name in (
                workflow.planner_agent,
                workflow.executor_agent,
                workflow.judge_agent,
            ):
                if ref_name not in agent_by_id:
                    raise WorkflowConfigError(
                        f"Workflow '{workflow_id}' references unknown agent '{ref_name}'."
                    )
            if workflow.expert_agent is not None and workflow.expert_agent not in agent_by_id:
                raise WorkflowConfigError(
                    f"Workflow '{workflow_id}' references unknown agent '{workflow.expert_agent}'."
                )
            planner = agent_by_id[workflow.planner_agent]
            executor = agent_by_id[workflow.executor_agent]
            judge = agent_by_id[workflow.judge_agent]
            expert = (
                agent_by_id[workflow.expert_agent]
                if workflow.expert_agent is not None
                else None
            )
            if planner.provider != "codex" or executor.provider != "codex":
                raise WorkflowConfigError(
                    f"Workflow '{workflow_id}' must use Codex agents for planner and executor."
                )
            if workflow.planner_agent != workflow.executor_agent:
                raise WorkflowConfigError(
                    f"Workflow '{workflow_id}' must use the same Codex agent for planner and executor in v1."
                )
            if judge.provider != "codex":
                raise WorkflowConfigError(
                    f"Workflow '{workflow_id}' must use a Codex agent for judging."
                )
            if expert is not None and expert.provider not in {"oracle", "codex"}:
                raise WorkflowConfigError(
                    f"Workflow '{workflow_id}' uses unsupported expert provider '{expert.provider}'."
                )
            workflows.append(workflow)
        if not workflows:
            raise WorkflowConfigError("Workflow config must define at least one workflow.")
        return sorted(workflows, key=lambda workflow: workflow.id)

    @staticmethod
    def _validate_agent(agent: AgentDefinition, raw_agent: dict[str, Any]) -> None:
        codex_keys = {
            "provider",
            "role",
            "startup_prompt",
            "description",
            "model",
            "model_provider",
            "reasoning_effort",
            "approval_policy",
            "sandbox_mode",
            "web_access",
            "service_tier",
        }
        oracle_keys = {
            "provider",
            "role",
            "startup_prompt",
            "description",
            "remote_host",
            "chatgpt_url",
            "model_strategy",
            "timeout_seconds",
            "prompt_char_limit",
        }
        allowed_keys = codex_keys if agent.provider == "codex" else oracle_keys
        unknown_keys = sorted(set(raw_agent) - allowed_keys)
        if unknown_keys:
            raise WorkflowConfigError(
                f"Agent '{agent.id}' uses unsupported options for provider '{agent.provider}': "
                + ", ".join(unknown_keys)
            )
````

## File: tests/test_workflow_config.py
````python
from __future__ import annotations

from pathlib import Path

import pytest

from shmocky.settings import AppSettings
from shmocky.workflow_config import WorkflowConfigError, WorkflowConfigLoader


def test_workflow_config_loader_reads_repo_toml(tmp_path: Path) -> None:
    config_path = tmp_path / "shmocky.toml"
    config_path.write_text(
        """
[agents.engineer]
provider = "codex"
role = "engineer"
model = "gpt-5.4"
reasoning_effort = "high"
approval_policy = "never"
sandbox_mode = "workspace-write"
web_access = "live"

[agents.expert]
provider = "oracle"
role = "expert"
chatgpt_url = "https://chatgpt.com/g/g-p-69cc59b46ad08191886f589993476e6f-codex/project"
model_strategy = "current"
prompt_char_limit = 64000

[agents.judge]
provider = "codex"
role = "judge"
model = "gpt-5.4"

[workflows.plan_execute_judge]
planner_agent = "engineer"
executor_agent = "engineer"
expert_agent = "expert"
judge_agent = "judge"
max_loops = 3
max_runtime_minutes = 20
max_judge_calls = 3
""".strip(),
        encoding="utf-8",
    )
    settings = AppSettings(
        workspace_root=tmp_path,
        workflow_config_path=config_path,
        codex_command="true",
        oracle_cli_command="true",
    )

    catalog = WorkflowConfigLoader(settings).load()

    assert catalog.loaded is True
    assert [agent.id for agent in catalog.agents] == ["engineer", "expert", "judge"]
    assert [workflow.id for workflow in catalog.workflows] == ["plan_execute_judge"]
    assert catalog.agents[1].prompt_char_limit == 64_000
    assert (
        catalog.agents[1].chatgpt_url
        == "https://chatgpt.com/g/g-p-69cc59b46ad08191886f589993476e6f-codex/project"
    )
    assert catalog.workflows[0].expert_agent == "expert"
    assert catalog.workflows[0].plan_prompt_template
    assert catalog.workflows[0].judge_prompt_template


def test_workflow_config_loader_rejects_split_codex_agents(tmp_path: Path) -> None:
    config_path = tmp_path / "shmocky.toml"
    config_path.write_text(
        """
[agents.planner]
provider = "codex"
role = "planner"

[agents.executor]
provider = "codex"
role = "engineer"

[agents.judge]
provider = "codex"
role = "judge"

[workflows.plan_execute_judge]
planner_agent = "planner"
executor_agent = "executor"
judge_agent = "judge"
""".strip(),
        encoding="utf-8",
    )
    settings = AppSettings(
        workspace_root=tmp_path,
        workflow_config_path=config_path,
        codex_command="true",
        oracle_cli_command="true",
    )

    with pytest.raises(WorkflowConfigError):
        WorkflowConfigLoader(settings).load()


def test_workflow_config_loader_rejects_oracle_judge(tmp_path: Path) -> None:
    config_path = tmp_path / "shmocky.toml"
    config_path.write_text(
        """
[agents.engineer]
provider = "codex"
role = "engineer"

[agents.judge]
provider = "oracle"
role = "judge"

[workflows.plan_execute_judge]
planner_agent = "engineer"
executor_agent = "engineer"
judge_agent = "judge"
""".strip(),
        encoding="utf-8",
    )
    settings = AppSettings(
        workspace_root=tmp_path,
        workflow_config_path=config_path,
        codex_command="true",
        oracle_cli_command="true",
    )

    with pytest.raises(WorkflowConfigError, match="Codex agent for judging"):
        WorkflowConfigLoader(settings).load()
````

## File: src/shmocky/settings.py
````python
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import AliasChoices, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SHMOCKY_",
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )

    codex_command: str = "codex"
    workspace_root: Path = Field(default_factory=Path.cwd)
    event_log_dir: Path = Field(default_factory=lambda: Path(".shmocky/events"))
    run_log_dir: Path = Field(default_factory=lambda: Path(".shmocky/runs"))
    workflow_config_path: Path = Field(default_factory=lambda: Path("shmocky.toml"))
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    request_timeout_seconds: float = 45.0
    experimental_api: bool = True
    allow_nested_target_dirs: bool = False
    approval_policy: Literal["untrusted", "on-failure", "on-request", "never"] = "never"
    sandbox_mode: Literal["read-only", "workspace-write", "danger-full-access"] = (
        "workspace-write"
    )
    oracle_cli_command: str = "npx"
    oracle_cli_package: str = "@steipete/oracle"
    oracle_remote_host: str = Field(
        default="https://oracle.yutani.tech:9473",
        validation_alias=AliasChoices("ORACLE_REMOTE_HOST", "SHMOCKY_ORACLE_REMOTE_HOST"),
    )
    oracle_remote_token: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("ORACLE_REMOTE_TOKEN", "SHMOCKY_ORACLE_REMOTE_TOKEN"),
    )
    oracle_engine: Literal["browser"] = "browser"
    oracle_browser_model_strategy: Literal["current", "ignore"] = "current"
    oracle_timeout_seconds: float = 3600.0
    oracle_prompt_char_limit: int = Field(default=20_000, ge=1_000, le=200_000)
    allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ]
    )

    @model_validator(mode="after")
    def validate_paths(self) -> "AppSettings":
        self.workspace_root = self.workspace_root.expanduser().resolve()
        self.event_log_dir = self.event_log_dir.expanduser()
        self.run_log_dir = self.run_log_dir.expanduser()
        self.workflow_config_path = self.workflow_config_path.expanduser()
        self.oracle_remote_host = self._normalize_oracle_remote_host(self.oracle_remote_host)
        if not self.event_log_dir.is_absolute():
            self.event_log_dir = (self.workspace_root / self.event_log_dir).resolve()
        if not self.run_log_dir.is_absolute():
            self.run_log_dir = (self.workspace_root / self.run_log_dir).resolve()
        if not self.workflow_config_path.is_absolute():
            self.workflow_config_path = (self.workspace_root / self.workflow_config_path).resolve()
        if not self.workspace_root.exists():
            raise ValueError(f"Workspace root does not exist: {self.workspace_root}")
        if shutil.which(self.codex_command) is None:
            raise ValueError(f"Could not find codex command on PATH: {self.codex_command}")
        if shutil.which(self.oracle_cli_command) is None:
            raise ValueError(
                f"Could not find Oracle CLI command on PATH: {self.oracle_cli_command}"
            )
        return self

    @staticmethod
    def _normalize_oracle_remote_host(value: str) -> str:
        normalized = value.strip().rstrip("/")
        if "://" in normalized:
            parts = urlsplit(normalized)
            normalized = parts.netloc
        if not normalized:
            raise ValueError("Oracle remote host must not be empty.")
        return normalized
````

## File: tests/test_oracle_agent.py
````python
from __future__ import annotations

import asyncio
from collections.abc import Sequence
from pathlib import Path

import pytest
from pydantic import SecretStr

from shmocky.models import OracleQueryRequest
from shmocky.oracle_agent import (
    OracleAgent,
    OracleAgentError,
    OracleNotConfiguredError,
    OraclePromptTooLongError,
)
from shmocky.settings import AppSettings


def test_oracle_settings_accept_existing_env_aliases(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ORACLE_REMOTE_HOST", "https://oracle.yutani.tech:9473")
    monkeypatch.setenv("ORACLE_REMOTE_TOKEN", "secret-token")
    settings = AppSettings(
        workspace_root=tmp_path,
        codex_command="true",
        oracle_cli_command="true",
    )

    assert settings.oracle_remote_token is not None
    assert settings.oracle_remote_token.get_secret_value() == "secret-token"
    assert settings.oracle_remote_host == "oracle.yutani.tech:9473"


def test_oracle_agent_configuration_detection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ORACLE_REMOTE_TOKEN", raising=False)
    configured = OracleAgent(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
            oracle_remote_token=SecretStr("secret-token"),
        )
    )
    unconfigured = OracleAgent(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
        )
    )

    assert configured.is_configured() is True
    assert unconfigured.is_configured() is False


def test_oracle_agent_resolves_relative_globs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ORACLE_REMOTE_TOKEN", raising=False)
    first = tmp_path / "src" / "alpha.py"
    second = tmp_path / "src" / "beta.py"
    first.parent.mkdir(parents=True)
    first.write_text("alpha", encoding="utf-8")
    second.write_text("beta", encoding="utf-8")

    agent = OracleAgent(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
            oracle_remote_token=SecretStr("secret-token"),
        )
    )

    attached_files = agent._resolve_files(["src/*.py"])

    assert attached_files == [str(first.resolve()), str(second.resolve())]


def test_oracle_agent_requires_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ORACLE_REMOTE_TOKEN", raising=False)
    agent = OracleAgent(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
        )
    )

    with pytest.raises(OracleNotConfiguredError):
        asyncio.run(agent.query(OracleQueryRequest(prompt="hello")))


def test_oracle_agent_enforces_default_prompt_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ORACLE_REMOTE_TOKEN", raising=False)
    agent = OracleAgent(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
            oracle_remote_token=SecretStr("secret-token"),
            oracle_prompt_char_limit=1_000,
        )
    )

    with pytest.raises(OraclePromptTooLongError):
        asyncio.run(agent.query(OracleQueryRequest(prompt="x" * 1_001)))


def test_oracle_agent_enforces_per_call_prompt_limit_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ORACLE_REMOTE_TOKEN", raising=False)
    agent = OracleAgent(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
            oracle_remote_token=SecretStr("secret-token"),
            oracle_prompt_char_limit=10_000,
        )
    )

    with pytest.raises(OraclePromptTooLongError):
        asyncio.run(
            agent.query(
                OracleQueryRequest(prompt="x" * 1_001),
                prompt_char_limit=1_000,
            )
        )


def test_oracle_agent_passes_chatgpt_url_to_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ORACLE_REMOTE_TOKEN", raising=False)
    captured: dict[str, object] = {}

    class FakeProcess:
        returncode = 0

        async def communicate(self) -> tuple[bytes, bytes]:
            return b"", b""

        def kill(self) -> None:
            return None

        async def wait(self) -> int:
            return 0

    async def fake_create_subprocess_exec(
        *command: str,
        cwd: str | None = None,
        stdout: object | None = None,
        stderr: object | None = None,
    ) -> FakeProcess:
        captured["command"] = command
        captured["cwd"] = cwd
        captured["stdout"] = stdout
        captured["stderr"] = stderr
        return FakeProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    agent = OracleAgent(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
            oracle_remote_token=SecretStr("secret-token"),
        )
    )
    monkeypatch.setattr(agent, "_read_output", lambda path: "expert answer")

    response = asyncio.run(
        agent.query(
            OracleQueryRequest(prompt="hello"),
            chatgpt_url="https://chatgpt.com/g/g-p-69cc59b46ad08191886f589993476e6f-codex/project",
        )
    )

    command = captured["command"]
    assert isinstance(command, Sequence)
    assert "--chatgpt-url" in command
    assert (
        command[command.index("--chatgpt-url") + 1]
        == "https://chatgpt.com/g/g-p-69cc59b46ad08191886f589993476e6f-codex/project"
    )
    assert response.answer == "expert answer"


def test_oracle_agent_rejects_absolute_attachment_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ORACLE_REMOTE_TOKEN", raising=False)
    outside = tmp_path.parent / "secret.txt"
    outside.write_text("secret", encoding="utf-8")

    agent = OracleAgent(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
            oracle_remote_token=SecretStr("secret-token"),
        )
    )

    with pytest.raises(OracleAgentError, match="workspace root"):
        agent._resolve_files([str(outside)])


def test_oracle_agent_rejects_parent_traversal_attachment_globs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ORACLE_REMOTE_TOKEN", raising=False)
    outside = tmp_path.parent / "secrets" / "note.txt"
    outside.parent.mkdir(parents=True, exist_ok=True)
    outside.write_text("secret", encoding="utf-8")

    agent = OracleAgent(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
            oracle_remote_token=SecretStr("secret-token"),
        )
    )

    with pytest.raises(OracleAgentError, match="workspace files"):
        agent._resolve_files(["../secrets/*.txt"])


def test_oracle_agent_cleans_up_output_file_on_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ORACLE_REMOTE_TOKEN", raising=False)
    output_path = tmp_path / ".shmocky" / "oracle" / "timeout-output.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("stale", encoding="utf-8")

    class FakeProcess:
        returncode = None
        killed = False

        async def communicate(self) -> tuple[bytes, bytes]:
            await asyncio.sleep(3600)
            return b"", b""

        def kill(self) -> None:
            self.killed = True
            self.returncode = -9

        async def wait(self) -> int:
            return -9

    async def fake_create_subprocess_exec(
        *command: str,
        cwd: str | None = None,
        stdout: object | None = None,
        stderr: object | None = None,
    ) -> FakeProcess:
        return FakeProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    agent = OracleAgent(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
            oracle_remote_token=SecretStr("secret-token"),
        )
    )
    monkeypatch.setattr(agent, "_allocate_output_path", lambda: output_path)

    with pytest.raises(OracleAgentError, match="timed out"):
        asyncio.run(agent.query(OracleQueryRequest(prompt="hello"), timeout_seconds=0.01))

    assert output_path.exists() is False


def test_oracle_agent_cleans_up_output_file_when_subprocess_start_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ORACLE_REMOTE_TOKEN", raising=False)
    output_path = tmp_path / ".shmocky" / "oracle" / "spawn-failure-output.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("stale", encoding="utf-8")

    async def fake_create_subprocess_exec(
        *command: str,
        cwd: str | None = None,
        stdout: object | None = None,
        stderr: object | None = None,
    ) -> object:
        raise OSError("spawn failed")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    agent = OracleAgent(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
            oracle_remote_token=SecretStr("secret-token"),
        )
    )
    monkeypatch.setattr(agent, "_allocate_output_path", lambda: output_path)

    with pytest.raises(OSError, match="spawn failed"):
        asyncio.run(agent.query(OracleQueryRequest(prompt="hello")))

    assert output_path.exists() is False
````

## File: shmocky.toml
````toml
[agents.engineer]
provider = "codex"
role = "engineer"
model = "gpt-5.3-codex-spark"
reasoning_effort = "medium"
approval_policy = "never"
sandbox_mode = "workspace-write"
web_access = "live"
startup_prompt = """
You are the primary engineering agent for a Shmocky workflow run.

Work in small, testable slices. Keep progress observable. If you are blocked, say exactly what is blocking you and what evidence supports that conclusion.
"""

[agents.expert]
provider = "oracle"
role = "expert"
chatgpt_url = "https://chatgpt.com/g/g-p-69cc59b46ad08191886f589993476e6f-codex/project"
model_strategy = "current"
timeout_seconds = 3600
prompt_char_limit = 40000
startup_prompt = """
You are the workflow expert advisor. Return plain text analysis and concrete suggestions only.
"""

[agents.judge]
provider = "codex"
role = "judge"
model = "gpt-5.3-codex-spark"
reasoning_effort = "medium"
approval_policy = "never"
sandbox_mode = "workspace-write"
web_access = "disabled"
startup_prompt = """
You are the workflow judge. Decide whether the run should continue, complete, or fail. Follow the workflow prompt's response format exactly.
"""

[workflows.plan_execute_judge]
kind = "linear_loop"
executor_agent = "engineer"
expert_agent = "expert"
judge_agent = "judge"
max_loops = 4
max_runtime_minutes = 45
max_judge_calls = 4
````

## File: apps/web/src/lib/types.ts
````typescript
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
````

## File: src/shmocky/oracle_agent.py
````python
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from time import monotonic

from .models import OracleQueryRequest, OracleQueryResponse
from .settings import AppSettings


class OracleAgentError(RuntimeError):
    pass


class OracleNotConfiguredError(OracleAgentError):
    pass


class OraclePromptTooLongError(OracleAgentError):
    pass


class OracleAgent:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._lock = asyncio.Lock()

    def is_configured(self) -> bool:
        return self._settings.oracle_remote_token is not None

    async def query(
        self,
        request: OracleQueryRequest,
        *,
        remote_host: str | None = None,
        chatgpt_url: str | None = None,
        model_strategy: str | None = None,
        timeout_seconds: float | None = None,
        prompt_char_limit: int | None = None,
    ) -> OracleQueryResponse:
        async with self._lock:
            return await self._run_query(
                request,
                remote_host=remote_host,
                chatgpt_url=chatgpt_url,
                model_strategy=model_strategy,
                timeout_seconds=timeout_seconds,
                prompt_char_limit=prompt_char_limit,
            )

    async def _run_query(
        self,
        request: OracleQueryRequest,
        *,
        remote_host: str | None,
        chatgpt_url: str | None,
        model_strategy: str | None,
        timeout_seconds: float | None,
        prompt_char_limit: int | None,
    ) -> OracleQueryResponse:
        token = self._settings.oracle_remote_token
        if token is None:
            raise OracleNotConfiguredError(
                "Oracle remote token is not configured. Set ORACLE_REMOTE_TOKEN in .env."
            )
        effective_prompt_limit = (
            prompt_char_limit or self._settings.oracle_prompt_char_limit
        )
        if len(request.prompt) > effective_prompt_limit:
            raise OraclePromptTooLongError(
                "Oracle prompt exceeds the configured character limit "
                f"({effective_prompt_limit})."
            )

        attached_files = self._resolve_files(request.files)
        output_path = self._allocate_output_path()
        try:
            effective_remote_host = self._settings._normalize_oracle_remote_host(
                remote_host or self._settings.oracle_remote_host
            )
            effective_chatgpt_url = chatgpt_url.strip() if chatgpt_url is not None else None
            effective_model_strategy = (
                model_strategy or self._settings.oracle_browser_model_strategy
            )
            effective_timeout_seconds = timeout_seconds or self._settings.oracle_timeout_seconds
            command = [
                self._settings.oracle_cli_command,
                "-y",
                self._settings.oracle_cli_package,
                "--engine",
                self._settings.oracle_engine,
                "--remote-host",
                effective_remote_host,
                "--remote-token",
                token.get_secret_value(),
                "--browser-model-strategy",
                effective_model_strategy,
                "--write-output",
                str(output_path),
            ]
            if effective_chatgpt_url:
                command.extend(["--chatgpt-url", effective_chatgpt_url])
            for path in attached_files:
                command.extend(["--file", path])
            command.extend(["-p", request.prompt])

            started_at = monotonic()
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=str(self._settings.workspace_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=effective_timeout_seconds,
                )
            except TimeoutError as exc:
                process.kill()
                await process.wait()
                raise OracleAgentError(
                    f"Oracle query timed out after {effective_timeout_seconds:.0f}s."
                ) from exc

            duration_seconds = monotonic() - started_at
            stdout_text = stdout_bytes.decode("utf-8", errors="replace").strip()
            stderr_text = stderr_bytes.decode("utf-8", errors="replace").strip()
            answer = self._read_output(output_path).strip()

            if process.returncode != 0:
                detail = stderr_text or stdout_text or f"Oracle exited with code {process.returncode}."
                raise OracleAgentError(detail)
            if not answer:
                raise OracleAgentError("Oracle exited successfully but did not produce a final answer.")

            return OracleQueryResponse(
                answer=answer,
                remote_host=effective_remote_host,
                duration_seconds=duration_seconds,
                attached_files=attached_files,
                stderr=stderr_text or None,
            )
        finally:
            output_path.unlink(missing_ok=True)

    def _resolve_files(self, patterns: list[str]) -> list[str]:
        attached_files: list[str] = []
        seen: set[Path] = set()
        workspace_root = self._settings.workspace_root.resolve()
        for pattern in patterns:
            base_pattern = pattern.strip()
            if not base_pattern:
                continue
            candidate_pattern = Path(base_pattern)
            if candidate_pattern.is_absolute():
                raise OracleAgentError(
                    "Oracle file attachments must stay within the configured workspace root."
                )
            matches = sorted(workspace_root.glob(base_pattern))
            accessible_matches: list[Path] = []
            for match in matches:
                resolved = match.resolve()
                if not resolved.is_relative_to(workspace_root):
                    continue
                accessible_matches.append(resolved)
            if not accessible_matches:
                raise OracleAgentError(
                    f"Oracle file pattern did not match any workspace files: {pattern}"
                )
            for resolved in accessible_matches:
                if not resolved.is_file() or resolved in seen:
                    continue
                seen.add(resolved)
                attached_files.append(str(resolved))
        return attached_files

    def _allocate_output_path(self) -> Path:
        output_dir = self._settings.workspace_root / ".shmocky" / "oracle"
        output_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            prefix="oracle-",
            suffix=".txt",
            dir=output_dir,
            delete=False,
        ) as handle:
            return Path(handle.name)

    def _read_output(self, output_path: Path) -> str:
        return output_path.read_text(encoding="utf-8")
````

## File: src/shmocky/main.py
````python
from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    DashboardSnapshot,
    OracleQueryRequest,
    OracleQueryResponse,
    PromptRequest,
    RunHistoryResponse,
    ServerRequestResolutionRequest,
    StreamEnvelope,
    WorkflowCatalogResponse,
    WorkflowRunRequest,
    WorkflowRunState,
    WorkflowSteerRequest,
)
from .oracle_agent import (
    OracleAgent,
    OracleAgentError,
    OracleNotConfiguredError,
    OraclePromptTooLongError,
)
from .settings import AppSettings
from .supervisor import WorkflowSupervisor, as_http_error


def create_app() -> FastAPI:
    settings = AppSettings()
    supervisor = WorkflowSupervisor(settings)
    oracle = OracleAgent(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        try:
            yield
        finally:
            await supervisor.shutdown()

    app = FastAPI(title="Shmocky", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    async def health() -> dict[str, object]:
        snapshot = supervisor.snapshot()
        catalog = supervisor.workflows_catalog()
        return {
            "backendOnline": snapshot.state.connection.backend_online,
            "codexConnected": snapshot.state.connection.codex_connected,
            "initialized": snapshot.state.connection.initialized,
            "oracleConfigured": oracle.is_configured(),
            "oracleRemoteHost": settings.oracle_remote_host,
            "workflowConfigLoaded": catalog.loaded,
            "workflowConfigPath": catalog.config_path,
            "workflowConfigError": catalog.error,
        }

    @app.get("/api/state", response_model=DashboardSnapshot)
    async def state() -> DashboardSnapshot:
        return supervisor.snapshot()

    @app.get("/api/workflows", response_model=WorkflowCatalogResponse)
    async def workflows() -> WorkflowCatalogResponse:
        return supervisor.workflows_catalog()

    @app.get("/api/runs/active", response_model=WorkflowRunState | None)
    async def active_run() -> WorkflowRunState | None:
        return supervisor.snapshot().state.workflow_run

    @app.get("/api/runs", response_model=RunHistoryResponse)
    async def runs_history() -> RunHistoryResponse:
        return supervisor.runs_history()

    @app.get("/api/runs/{run_id}", response_model=DashboardSnapshot)
    async def run_snapshot(run_id: str) -> DashboardSnapshot:
        try:
            return supervisor.load_run_snapshot(run_id)
        except Exception as exc:
            raise as_http_error(exc) from exc

    @app.post("/api/thread/start", response_model=DashboardSnapshot)
    async def start_thread() -> DashboardSnapshot:
        try:
            return await supervisor.start_thread()
        except Exception as exc:
            raise as_http_error(exc) from exc

    @app.post("/api/turns", response_model=DashboardSnapshot)
    async def create_turn(payload: PromptRequest) -> DashboardSnapshot:
        try:
            return await supervisor.send_prompt(payload.prompt)
        except Exception as exc:
            raise as_http_error(exc) from exc

    @app.post("/api/turns/interrupt", response_model=DashboardSnapshot)
    async def interrupt_turn() -> DashboardSnapshot:
        try:
            return await supervisor.interrupt_turn()
        except Exception as exc:
            raise as_http_error(exc) from exc

    @app.post(
        "/api/server-requests/{request_id}/resolve",
        response_model=DashboardSnapshot,
    )
    async def resolve_server_request(
        request_id: str,
        payload: ServerRequestResolutionRequest,
    ) -> DashboardSnapshot:
        try:
            return await supervisor.resolve_server_request(request_id, payload)
        except Exception as exc:
            raise as_http_error(exc) from exc

    @app.post("/api/oracle/query", response_model=OracleQueryResponse)
    async def oracle_query(payload: OracleQueryRequest) -> OracleQueryResponse:
        try:
            remote_host: str | None = None
            chatgpt_url: str | None = None
            model_strategy: str | None = None
            timeout_seconds: float | None = None
            prompt_char_limit: int | None = None
            if payload.agent_id is not None:
                catalog = supervisor.workflows_catalog()
                if not catalog.loaded:
                    raise HTTPException(
                        status_code=503,
                        detail=(
                            "Workflow config is not available, so Oracle agent settings "
                            "cannot be resolved."
                        ),
                    )
                oracle_agent = next(
                    (
                        agent
                        for agent in catalog.agents
                        if agent.id == payload.agent_id and agent.provider == "oracle"
                    ),
                    None,
                )
                if oracle_agent is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Unknown Oracle agent '{payload.agent_id}'.",
                    )
                remote_host = oracle_agent.remote_host
                chatgpt_url = oracle_agent.chatgpt_url
                model_strategy = oracle_agent.model_strategy
                timeout_seconds = oracle_agent.timeout_seconds
                prompt_char_limit = oracle_agent.prompt_char_limit
            return await oracle.query(
                payload,
                remote_host=remote_host,
                chatgpt_url=chatgpt_url,
                model_strategy=model_strategy,
                timeout_seconds=timeout_seconds,
                prompt_char_limit=prompt_char_limit,
            )
        except OracleNotConfiguredError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except OraclePromptTooLongError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except OracleAgentError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.post("/api/runs", response_model=DashboardSnapshot)
    async def start_run(payload: WorkflowRunRequest) -> DashboardSnapshot:
        try:
            return await supervisor.start_run(payload)
        except Exception as exc:
            raise as_http_error(exc) from exc

    @app.post("/api/runs/active/pause", response_model=DashboardSnapshot)
    async def pause_run() -> DashboardSnapshot:
        try:
            return await supervisor.pause_run()
        except Exception as exc:
            raise as_http_error(exc) from exc

    @app.post("/api/runs/active/resume", response_model=DashboardSnapshot)
    async def resume_run() -> DashboardSnapshot:
        try:
            return await supervisor.resume_run()
        except Exception as exc:
            raise as_http_error(exc) from exc

    @app.post("/api/runs/active/stop", response_model=DashboardSnapshot)
    async def stop_run() -> DashboardSnapshot:
        try:
            return await supervisor.stop_run()
        except Exception as exc:
            raise as_http_error(exc) from exc

    @app.post("/api/runs/active/steer", response_model=DashboardSnapshot)
    async def steer_run(payload: WorkflowSteerRequest) -> DashboardSnapshot:
        try:
            return await supervisor.steer_run(payload)
        except Exception as exc:
            raise as_http_error(exc) from exc

    @app.websocket("/api/events")
    async def events(websocket: WebSocket) -> None:
        await websocket.accept()
        queue = await supervisor.subscribe()
        try:
            await websocket.send_json(
                StreamEnvelope(
                    type="state",
                    state=supervisor.snapshot().state,
                    event=None,
                    workflow_event=None,
                ).model_dump(mode="json"),
            )
            while True:
                envelope = await queue.get()
                await websocket.send_json(envelope.model_dump(mode="json"))
        except WebSocketDisconnect:
            return
        finally:
            supervisor.unsubscribe(queue)

    return app


app = create_app()


def main() -> None:
    settings = AppSettings()
    uvicorn.run(
        "shmocky.main:app",
        host=settings.api_host,
        port=settings.api_port,
        factory=False,
    )


if __name__ == "__main__":
    main()
````

## File: src/shmocky/models.py
````python
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

type EventDirection = Literal["outbound", "inbound", "internal"]
type EventChannel = Literal["rpc", "stderr", "lifecycle"]
type EventMessageType = Literal[
    "request",
    "response",
    "notification",
    "server_request",
    "stderr",
    "lifecycle",
    "unknown",
]
type ApprovalPolicy = Literal["untrusted", "on-failure", "on-request", "never"]
type SandboxMode = Literal["read-only", "workspace-write", "danger-full-access"]
type ReasoningEffort = Literal["none", "minimal", "low", "medium", "high", "xhigh"]
type WebAccessMode = Literal["disabled", "cached", "live"]
type AgentProvider = Literal["codex", "oracle"]
type WorkflowKind = Literal["linear_loop"]
type WorkflowDecisionType = Literal["continue", "complete", "fail"]
type WorkflowRunStatus = Literal[
    "idle",
    "starting",
    "running",
    "paused",
    "completed",
    "failed",
    "stopped",
]
type WorkflowPhase = Literal[
    "idle",
    "planning",
    "executing",
    "advising",
    "judging",
    "paused",
    "completed",
    "failed",
    "stopped",
]


class ConnectionState(BaseModel):
    backend_online: bool = True
    codex_connected: bool = False
    initialized: bool = False
    app_server_pid: int | None = None
    app_server_user_agent: str | None = None
    codex_home: str | None = None
    platform_family: str | None = None
    platform_os: str | None = None
    last_error: str | None = None


class ThreadState(BaseModel):
    id: str
    status: str = "idle"
    cwd: str | None = None
    model: str | None = None
    model_provider: str | None = None
    approval_policy: str | None = None
    sandbox_mode: str | None = None
    reasoning_effort: str | None = None
    created_at: int | None = None
    updated_at: int | None = None


class TurnState(BaseModel):
    id: str
    status: str = "pending"
    last_event_at: datetime | None = None
    error: str | None = None


class TranscriptItem(BaseModel):
    item_id: str
    role: Literal["user", "assistant"]
    text: str = ""
    phase: str | None = None
    status: Literal["streaming", "completed"] = "completed"
    turn_id: str | None = None


class PendingServerRequest(BaseModel):
    request_id: str
    method: str
    params: dict[str, Any] | None = None
    noted_at: datetime


class DashboardState(BaseModel):
    workspace_root: str
    event_log_path: str
    connection: ConnectionState
    thread: ThreadState | None = None
    turn: TurnState | None = None
    transcript: list[TranscriptItem] = Field(default_factory=list)
    mcp_servers: dict[str, str] = Field(default_factory=dict)
    rate_limits: dict[str, Any] | None = None
    pending_server_request: PendingServerRequest | None = None
    workflow_run: "WorkflowRunState | None" = None


class RawEventRecord(BaseModel):
    sequence: int
    event_id: str
    recorded_at: datetime
    direction: EventDirection
    channel: EventChannel
    message_type: EventMessageType
    method: str | None = None
    payload: Any


class DashboardSnapshot(BaseModel):
    state: DashboardState
    recent_events: list[RawEventRecord] = Field(default_factory=list)
    recent_workflow_events: list["WorkflowEventRecord"] = Field(default_factory=list)


class StreamEnvelope(BaseModel):
    type: Literal["event", "workflow_event", "state"]
    state: DashboardState
    event: RawEventRecord | None = None
    workflow_event: "WorkflowEventRecord | None" = None


class PromptRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=20_000)


class ServerRequestResolutionRequest(BaseModel):
    result: Any = None


class OracleQueryRequest(BaseModel):
    prompt: str = Field(min_length=1)
    agent_id: str | None = Field(default=None, min_length=1, max_length=200)
    files: list[str] = Field(default_factory=list, max_length=64)


class OracleQueryResponse(BaseModel):
    answer: str
    remote_host: str
    duration_seconds: float
    attached_files: list[str] = Field(default_factory=list)
    stderr: str | None = None


class CodexAgentConfig(BaseModel):
    role: str
    startup_prompt: str | None = None
    description: str | None = None
    model: str | None = None
    model_provider: str | None = None
    reasoning_effort: ReasoningEffort | None = None
    approval_policy: ApprovalPolicy = "never"
    sandbox_mode: SandboxMode = "workspace-write"
    web_access: WebAccessMode = "disabled"
    service_tier: Literal["fast", "flex"] | None = None


class OracleAgentConfig(BaseModel):
    role: str
    startup_prompt: str | None = None
    description: str | None = None
    remote_host: str | None = None
    chatgpt_url: str | None = None
    model_strategy: Literal["current", "ignore"] = "current"
    timeout_seconds: float | None = None
    prompt_char_limit: int | None = Field(default=None, ge=1_000, le=200_000)


class AgentDefinition(BaseModel):
    id: str
    provider: AgentProvider
    role: str
    startup_prompt: str | None = None
    description: str | None = None
    model: str | None = None
    model_provider: str | None = None
    reasoning_effort: ReasoningEffort | None = None
    approval_policy: ApprovalPolicy | None = None
    sandbox_mode: SandboxMode | None = None
    web_access: WebAccessMode | None = None
    service_tier: Literal["fast", "flex"] | None = None
    remote_host: str | None = None
    chatgpt_url: str | None = None
    model_strategy: Literal["current", "ignore"] | None = None
    timeout_seconds: float | None = None
    prompt_char_limit: int | None = Field(default=None, ge=1_000, le=200_000)


class WorkflowDefinition(BaseModel):
    id: str
    kind: WorkflowKind = "linear_loop"
    planner_agent: str
    executor_agent: str
    expert_agent: str | None = None
    judge_agent: str
    plan_prompt_template: str
    execute_prompt_template: str
    expert_prompt_template: str | None = None
    judge_prompt_template: str
    max_loops: int = Field(default=4, ge=1, le=100)
    max_runtime_minutes: int = Field(default=30, ge=1, le=24 * 60)
    max_judge_calls: int = Field(default=4, ge=1, le=100)


class WorkflowCatalogResponse(BaseModel):
    config_path: str
    loaded: bool
    error: str | None = None
    agents: list[AgentDefinition] = Field(default_factory=list)
    workflows: list[WorkflowDefinition] = Field(default_factory=list)


class RunHistoryEntry(BaseModel):
    id: str
    run_name: str | None = None
    workflow_id: str
    target_dir: str
    status: WorkflowRunStatus
    phase: WorkflowPhase
    started_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    last_judge_decision: WorkflowDecisionType | None = None
    last_judge_summary: str | None = None
    last_error: str | None = None


class RunHistoryResponse(BaseModel):
    runs: list[RunHistoryEntry] = Field(default_factory=list)


class OracleResumeCheckpoint(BaseModel):
    agent_label: Literal["expert", "judge"]
    agent_id: str
    thread_id: str
    loop_index: int = Field(ge=1)
    prompt: str = Field(min_length=1, max_length=50_000)
    detail: str | None = None
    noted_at: datetime


class WorkflowRunRequest(BaseModel):
    run_name: str | None = Field(default=None, min_length=1, max_length=200)
    workflow_id: str = Field(min_length=1, max_length=200)
    target_dir: str = Field(min_length=1, max_length=4_000)
    prompt: str = Field(min_length=1, max_length=20_000)


class WorkflowSteerRequest(BaseModel):
    note: str = Field(min_length=1, max_length=8_000)


class JudgeDecision(BaseModel):
    decision: WorkflowDecisionType
    summary: str = Field(min_length=1, max_length=8_000)
    next_prompt: str | None = Field(default=None, max_length=20_000)
    completion_note: str | None = Field(default=None, max_length=8_000)
    failure_reason: str | None = Field(default=None, max_length=8_000)


class WorkflowRunState(BaseModel):
    id: str
    run_name: str | None = Field(default=None, max_length=200)
    workflow_id: str
    target_dir: str
    goal: str
    status: WorkflowRunStatus = "starting"
    phase: WorkflowPhase = "idle"
    codex_agent_id: str
    judge_agent_id: str
    started_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    current_loop: int = 0
    max_loops: int
    judge_calls: int = 0
    max_judge_calls: int
    max_runtime_minutes: int
    expert_agent_id: str | None = None
    last_plan: str | None = None
    last_codex_output: str | None = None
    last_expert_assessment: str | None = None
    last_judge_decision: WorkflowDecisionType | None = None
    last_judge_summary: str | None = None
    last_continuation_prompt: str | None = Field(default=None, max_length=20_000)
    oracle_resume_checkpoint: OracleResumeCheckpoint | None = None
    last_error: str | None = None
    pause_requested: bool = False
    stop_requested: bool = False
    pending_steering_notes: list[str] = Field(default_factory=list)
    recent_steering_notes: list[str] = Field(default_factory=list)


class WorkflowEventRecord(BaseModel):
    sequence: int
    event_id: str
    recorded_at: datetime
    kind: str
    message: str
    payload: Any = None
````

## File: tests/test_supervisor.py
````python
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import subprocess
from pathlib import Path
from typing import Any, cast

import pytest

from shmocky.bridge import BridgeError, CodexAppServerBridge
from shmocky.event_store import WorkflowEventStore
from shmocky.models import (
    ConnectionState,
    DashboardSnapshot,
    DashboardState,
    OracleResumeCheckpoint,
    PendingServerRequest,
    ServerRequestResolutionRequest,
    ThreadState,
    TranscriptItem,
    WorkflowEventRecord,
    WorkflowRunRequest,
    WorkflowRunState,
)
from shmocky.settings import AppSettings
from shmocky.supervisor import LoadedRunContext, RunResources, WorkflowSupervisor, WorkflowSupervisorError


def test_supervisor_extract_json_from_fenced_answer() -> None:
    payload = WorkflowSupervisor._extract_json(
        """```json
{
  "decision": "continue",
  "summary": "Need one more step.",
  "next_prompt": "Run the tests and fix the failure."
}
```"""
    )

    assert '"decision": "continue"' in payload


def test_supervisor_repairs_judge_payload_with_unescaped_quotes_in_next_prompt() -> None:
    decision = WorkflowSupervisor._parse_judge_decision(
        '{"decision":"continue","summary":"Need one more step.",'
        '"next_prompt":"Preserve "lowest winning nonce" semantics while tuning chunk sizing."}'
    )

    assert decision.decision == "continue"
    assert decision.summary == "Need one more step."
    assert (
        decision.next_prompt
        == 'Preserve "lowest winning nonce" semantics while tuning chunk sizing.'
    )


def test_supervisor_parses_labeled_text_judge_response() -> None:
    decision = WorkflowSupervisor._parse_judge_decision(
        """Decision: continue
Summary: Need one more implementation slice.
Next prompt:
Continue from the current repository state.

Focus on benchmark realism and preserve correctness.
"""
    )

    assert decision.decision == "continue"
    assert decision.summary == "Need one more implementation slice."
    assert decision.next_prompt == (
        "Continue from the current repository state.\n\n"
        "Focus on benchmark realism and preserve correctness."
    )


def test_supervisor_render_template_preserves_literal_json_braces() -> None:
    rendered = WorkflowSupervisor._render_template(
        'Return {"decision":"complete"} and {judge_bundle}',
        judge_bundle="BUNDLE",
    )

    assert rendered == 'Return {"decision":"complete"} and BUNDLE'


def test_supervisor_render_judge_prompt_fits_oracle_limit() -> None:
    prompt_limit = 20_000
    prompt = WorkflowSupervisor._render_judge_prompt(
        "Context:\n{judge_bundle}",
        prompt_limit=prompt_limit,
        goal="goal",
        plan="plan",
        last_output="output",
        judge_bundle="X" * (prompt_limit + 5_000),
    )

    assert len(prompt) <= prompt_limit
    assert prompt.startswith("Context:\n")


def test_supervisor_rejects_target_inside_workspace_root(tmp_path: Path) -> None:
    config_path = tmp_path / "shmocky.toml"
    config_path.write_text(
        """
[agents.engineer]
provider = "codex"
role = "engineer"

[agents.judge]
provider = "oracle"
role = "judge"

[workflows.plan_execute_judge]
planner_agent = "engineer"
executor_agent = "engineer"
judge_agent = "judge"
""".strip(),
        encoding="utf-8",
    )
    target_dir = tmp_path / "var" / "test"
    target_dir.mkdir(parents=True)
    supervisor = WorkflowSupervisor(
        AppSettings(
            workspace_root=tmp_path,
            workflow_config_path=config_path,
            codex_command="true",
            oracle_cli_command="true",
        )
    )

    with pytest.raises(WorkflowSupervisorError, match="inside the Shmocky workspace"):
        supervisor._validate_target_dir(target_dir)


def test_supervisor_rejects_target_nested_in_other_repo(tmp_path: Path) -> None:
    config_path = tmp_path / "config-home" / "shmocky.toml"
    config_path.parent.mkdir()
    config_path.write_text(
        """
[agents.engineer]
provider = "codex"
role = "engineer"

[agents.judge]
provider = "oracle"
role = "judge"

[workflows.plan_execute_judge]
planner_agent = "engineer"
executor_agent = "engineer"
judge_agent = "judge"
""".strip(),
        encoding="utf-8",
    )
    repo_root = tmp_path / "external-repo"
    target_dir = repo_root / "nested" / "workdir"
    target_dir.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(repo_root)], check=True)
    supervisor = WorkflowSupervisor(
        AppSettings(
            workspace_root=config_path.parent,
            workflow_config_path=config_path,
            codex_command="true",
            oracle_cli_command="true",
        )
    )

    with pytest.raises(
        WorkflowSupervisorError,
        match="nested inside another git repository",
    ):
        supervisor._validate_target_dir(target_dir)


def test_supervisor_lists_and_loads_persisted_run_snapshots(tmp_path: Path) -> None:
    run_dir = tmp_path / ".shmocky" / "runs" / "20260331T120000Z-abcdef12"
    run_dir.mkdir(parents=True)
    started_at = datetime(2026, 3, 31, 12, 0, tzinfo=UTC)
    snapshot = DashboardSnapshot(
        state=DashboardState(
            workspace_root=str(tmp_path / "repo"),
            event_log_path=str(run_dir / "codex-events" / "events.jsonl"),
            connection=ConnectionState(backend_online=True, codex_connected=False),
            workflow_run=WorkflowRunState(
                id="20260331T120000Z-abcdef12",
                run_name="workflow testing xyz",
                workflow_id="plan_execute_judge",
                target_dir=str(tmp_path / "repo"),
                goal="Ship the feature.",
                status="completed",
                phase="completed",
                codex_agent_id="engineer",
                judge_agent_id="judge",
                started_at=started_at,
                updated_at=started_at,
                completed_at=started_at,
                max_loops=4,
                max_judge_calls=4,
                max_runtime_minutes=45,
                last_judge_decision="complete",
                last_judge_summary="Done.",
            ),
        ),
        recent_events=[],
        recent_workflow_events=[],
    )
    (run_dir / WorkflowSupervisor.RUN_SNAPSHOT_FILENAME).write_text(
        snapshot.model_dump_json(indent=2),
        encoding="utf-8",
    )
    supervisor = WorkflowSupervisor(
        AppSettings(
            workspace_root=tmp_path,
            run_log_dir=tmp_path / ".shmocky" / "runs",
            codex_command="true",
            oracle_cli_command="true",
        )
    )

    history = supervisor.runs_history()
    loaded = supervisor.load_run_snapshot("20260331T120000Z-abcdef12")

    assert [entry.id for entry in history.runs] == ["20260331T120000Z-abcdef12"]
    assert history.runs[0].run_name == "workflow testing xyz"
    assert history.runs[0].last_judge_summary == "Done."
    assert loaded.state.workflow_run is not None
    assert loaded.state.workflow_run.status == "completed"


def test_supervisor_debounces_snapshot_flushes_for_bursty_updates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_dir = tmp_path / ".shmocky" / "runs" / "run-1"
    run_dir.mkdir(parents=True)
    started_at = datetime(2026, 4, 1, 12, 0, tzinfo=UTC)
    supervisor = WorkflowSupervisor(
        AppSettings(
            workspace_root=tmp_path,
            run_log_dir=tmp_path / ".shmocky" / "runs",
            codex_command="true",
            oracle_cli_command="true",
        )
    )
    supervisor._resources = RunResources(
        run_dir=run_dir,
        workflow_event_store=WorkflowEventStore(run_dir / "workflow-events.jsonl"),
    )
    supervisor._run_state = WorkflowRunState(
        id="run-1",
        run_name="burst test",
        workflow_id="plan_execute_judge",
        target_dir=str(tmp_path / "repo"),
        goal="Keep snapshot writes cheap.",
        status="running",
        phase="executing",
        codex_agent_id="engineer",
        judge_agent_id="judge",
        started_at=started_at,
        updated_at=started_at,
        max_loops=4,
        max_judge_calls=4,
        max_runtime_minutes=45,
    )

    writes: list[Path] = []

    def fake_write_snapshot_file(path: Path, payload: str) -> None:
        writes.append(path)

    monkeypatch.setattr(
        WorkflowSupervisor,
        "_write_snapshot_file",
        staticmethod(fake_write_snapshot_file),
    )

    async def exercise() -> None:
        supervisor._stage_run_snapshot()
        supervisor._stage_run_snapshot()
        supervisor._stage_run_snapshot()
        await asyncio.sleep(supervisor.SNAPSHOT_FLUSH_DEBOUNCE_SECONDS * 3)

    asyncio.run(exercise())

    assert writes == [run_dir / WorkflowSupervisor.RUN_SNAPSHOT_FILENAME]


def test_supervisor_snapshot_uses_archived_completed_run_when_bridge_is_gone(
    tmp_path: Path,
) -> None:
    started_at = datetime(2026, 3, 31, 12, 0, tzinfo=UTC)
    supervisor = WorkflowSupervisor(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
        )
    )
    supervisor._run_state = WorkflowRunState(
        id="run-1",
        run_name="named run",
        workflow_id="plan_execute_judge",
        target_dir=str(tmp_path / "repo"),
        goal="Explain the run.",
        status="failed",
        phase="failed",
        codex_agent_id="engineer",
        judge_agent_id="judge",
        started_at=started_at,
        updated_at=started_at,
        completed_at=started_at,
        max_loops=4,
        max_judge_calls=4,
        max_runtime_minutes=45,
        last_continuation_prompt="Run the benchmark again with the new flag.",
        last_error="Loop budget exceeded.",
    )
    supervisor._archived_snapshot = DashboardSnapshot.model_validate(
        {
            "state": {
                "workspace_root": str(tmp_path / "repo"),
                "event_log_path": str(tmp_path / ".shmocky" / "events"),
                "connection": {
                    "backend_online": True,
                    "codex_connected": True,
                    "initialized": True,
                    "app_server_pid": 123,
                },
                "thread": {"id": "thread-1", "status": "idle"},
                "transcript": [
                    {
                        "item_id": "assistant-1",
                        "role": "assistant",
                        "text": "Investigated the repository.",
                        "status": "completed",
                        "turn_id": "turn-1",
                    }
                ],
                "workflow_run": supervisor._run_state.model_dump(mode="json"),
            },
            "recent_events": [],
            "recent_workflow_events": [],
        }
    )

    snapshot = supervisor.snapshot()

    assert snapshot.state.connection.codex_connected is False
    assert snapshot.state.connection.app_server_pid is None
    assert snapshot.state.workflow_run is not None
    assert snapshot.state.workflow_run.last_error == "Loop budget exceeded."
    assert (
        snapshot.state.workflow_run.last_continuation_prompt
        == "Run the benchmark again with the new flag."
    )
    assert [item.text for item in snapshot.state.transcript] == [
        "Investigated the repository."
    ]


def test_supervisor_resolves_pending_server_request(tmp_path: Path) -> None:
    noted_at = datetime(2026, 4, 1, 12, 0, tzinfo=UTC)
    supervisor = WorkflowSupervisor(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
        )
    )

    class DummyBridge:
        def __init__(self) -> None:
            self.calls: list[tuple[str, object]] = []
            self._snapshot = DashboardSnapshot(
                state=DashboardState(
                    workspace_root=str(tmp_path),
                    event_log_path=str(tmp_path / ".shmocky" / "events"),
                    connection=ConnectionState(backend_online=True, codex_connected=True),
                    pending_server_request=PendingServerRequest(
                        request_id="req-1",
                        method="item/commandExecution/requestApproval",
                        params={"command": "git status"},
                        noted_at=noted_at,
                    ),
                ),
                recent_events=[],
                recent_workflow_events=[],
            )

        def snapshot(self) -> DashboardSnapshot:
            return self._snapshot

        async def resolve_server_request(self, request_id: str, *, result: object) -> DashboardSnapshot:
            self.calls.append((request_id, result))
            return self._snapshot

    bridge = DummyBridge()
    supervisor._bridge = cast(CodexAppServerBridge, bridge)

    snapshot = asyncio.run(
        supervisor.resolve_server_request(
            "req-1",
            ServerRequestResolutionRequest(result={"decision": "accept"}),
        )
    )

    assert bridge.calls == [("req-1", {"decision": "accept"})]
    assert snapshot.state.pending_server_request is not None
    assert snapshot.state.pending_server_request.request_id == "req-1"


def test_supervisor_pauses_and_resumes_after_oracle_failure(tmp_path: Path) -> None:
    started_at = datetime(2026, 4, 1, 12, 0, tzinfo=UTC)
    supervisor = WorkflowSupervisor(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
        )
    )
    supervisor._run_state = WorkflowRunState(
        id="run-1",
        run_name="oracle wait test",
        workflow_id="plan_execute_judge",
        target_dir=str(tmp_path),
        goal="Keep waiting for Oracle.",
        status="running",
        phase="advising",
        codex_agent_id="engineer",
        expert_agent_id="expert",
        judge_agent_id="judge",
        started_at=started_at,
        updated_at=started_at,
        max_loops=4,
        max_judge_calls=4,
        max_runtime_minutes=45,
    )

    async def exercise() -> None:
        supervisor._archived_snapshot = DashboardSnapshot(
            state=DashboardState(
                workspace_root=str(tmp_path),
                event_log_path=str(tmp_path / ".shmocky" / "events"),
                connection=ConnectionState(backend_online=True, codex_connected=False),
                thread=ThreadState(id="thread-1", status="idle"),
                workflow_run=supervisor._run_state,
            ),
            recent_events=[],
            recent_workflow_events=[],
        )
        task = asyncio.create_task(
            supervisor._pause_for_oracle_failure(
                agent_label="expert",
                agent_id="expert",
                prompt="Assess the current run.",
                detail="Oracle query timed out after 3600s.",
            )
        )
        supervisor._run_task = task
        await asyncio.sleep(0)
        assert supervisor._run_state is not None
        assert supervisor._run_state.status == "paused"
        assert supervisor._run_state.phase == "paused"
        assert supervisor._run_state.last_error is not None
        assert "Oracle expert failed and the run is paused" in supervisor._run_state.last_error

        await supervisor.resume_run()
        await task
        supervisor._run_task = None

    asyncio.run(exercise())

    assert supervisor._run_state is not None
    assert supervisor._run_state.status == "running"


def test_supervisor_restores_resumable_oracle_pause_from_disk(tmp_path: Path) -> None:
    run_dir = tmp_path / ".shmocky" / "runs" / "20260401T120000Z-resume123"
    run_dir.mkdir(parents=True)
    started_at = datetime(2026, 4, 1, 12, 0, tzinfo=UTC)
    noted_at = datetime(2026, 4, 1, 12, 30, tzinfo=UTC)
    snapshot = DashboardSnapshot(
        state=DashboardState(
            workspace_root=str(tmp_path / "repo"),
            event_log_path=str(run_dir / "codex-events" / "events.jsonl"),
            connection=ConnectionState(backend_online=True, codex_connected=True),
            thread=ThreadState(id="thread-1", status="idle"),
            transcript=[
                TranscriptItem(
                    item_id="assistant-1",
                    role="assistant",
                    text="Investigated the repo.",
                    status="completed",
                    turn_id="turn-1",
                )
            ],
            workflow_run=WorkflowRunState(
                id="20260401T120000Z-resume123",
                run_name="oracle resume",
                workflow_id="plan_execute_judge",
                target_dir=str(tmp_path / "repo"),
                goal="Keep the run resumable.",
                status="paused",
                phase="paused",
                codex_agent_id="engineer",
                expert_agent_id="expert",
                judge_agent_id="judge",
                started_at=started_at,
                updated_at=noted_at,
                current_loop=2,
                max_loops=4,
                judge_calls=1,
                max_judge_calls=4,
                max_runtime_minutes=45,
                last_plan="Plan",
                last_codex_output="Codex output",
                oracle_resume_checkpoint=OracleResumeCheckpoint(
                    agent_label="expert",
                    agent_id="expert",
                    thread_id="thread-1",
                    loop_index=2,
                    prompt="Assess the current run.",
                    detail="Oracle timed out.",
                    noted_at=noted_at,
                ),
                last_error="Oracle expert failed and the run is paused: Oracle timed out.",
            ),
        ),
        recent_events=[],
        recent_workflow_events=[],
    )
    (run_dir / WorkflowSupervisor.RUN_SNAPSHOT_FILENAME).write_text(
        snapshot.model_dump_json(indent=2),
        encoding="utf-8",
    )
    (run_dir / "workflow-events.jsonl").write_text(
        WorkflowEventRecord(
            sequence=1,
            event_id="event-1",
            recorded_at=noted_at,
            kind="oracle_blocked",
            message="Oracle expert failed; run paused until operator resume.",
            payload={"agent": "expert"},
        ).model_dump_json()
        + "\n",
        encoding="utf-8",
    )

    supervisor = WorkflowSupervisor(
        AppSettings(
            workspace_root=tmp_path,
            run_log_dir=tmp_path / ".shmocky" / "runs",
            codex_command="true",
            oracle_cli_command="true",
        )
    )

    restored = supervisor.snapshot()

    assert restored.state.workflow_run is not None
    assert restored.state.workflow_run.oracle_resume_checkpoint is not None
    assert restored.state.workflow_run.oracle_resume_checkpoint.thread_id == "thread-1"
    assert restored.state.thread is not None
    assert restored.state.thread.id == "thread-1"
    assert restored.state.transcript[0].text == "Investigated the repo."


def test_supervisor_resume_run_restarts_paused_oracle_run_from_manifest(tmp_path: Path) -> None:
    run_dir = tmp_path / ".shmocky" / "runs" / "20260401T120000Z-resume124"
    run_dir.mkdir(parents=True)
    started_at = datetime(2026, 4, 1, 12, 0, tzinfo=UTC)
    noted_at = datetime(2026, 4, 1, 12, 30, tzinfo=UTC)
    snapshot = DashboardSnapshot(
        state=DashboardState(
            workspace_root=str(tmp_path / "repo"),
            event_log_path=str(run_dir / "codex-events" / "events.jsonl"),
            connection=ConnectionState(backend_online=True, codex_connected=False),
            thread=ThreadState(id="thread-9", status="idle"),
            transcript=[
                TranscriptItem(
                    item_id="assistant-1",
                    role="assistant",
                    text="Investigated the repo.",
                    status="completed",
                    turn_id="turn-1",
                )
            ],
            workflow_run=WorkflowRunState(
                id="20260401T120000Z-resume124",
                run_name="oracle resume",
                workflow_id="plan_execute_judge",
                target_dir=str(tmp_path / "repo"),
                goal="Keep the run resumable.",
                status="paused",
                phase="paused",
                codex_agent_id="engineer",
                expert_agent_id="expert",
                judge_agent_id="judge",
                started_at=started_at,
                updated_at=noted_at,
                current_loop=2,
                max_loops=4,
                judge_calls=1,
                max_judge_calls=4,
                max_runtime_minutes=45,
                last_plan="Plan",
                last_codex_output="Codex output",
                oracle_resume_checkpoint=OracleResumeCheckpoint(
                    agent_label="expert",
                    agent_id="expert",
                    thread_id="thread-9",
                    loop_index=2,
                    prompt="Assess the current run.",
                    detail="Oracle timed out.",
                    noted_at=noted_at,
                ),
                last_error="Oracle expert failed and the run is paused: Oracle timed out.",
            ),
        ),
        recent_events=[],
        recent_workflow_events=[],
    )
    (run_dir / WorkflowSupervisor.RUN_SNAPSHOT_FILENAME).write_text(
        snapshot.model_dump_json(indent=2),
        encoding="utf-8",
    )
    (run_dir / WorkflowSupervisor.RUN_MANIFEST_FILENAME).write_text(
        """{
  "runId": "20260401T120000Z-resume124",
  "workflow": {
    "id": "plan_execute_judge",
    "kind": "linear_loop",
    "planner_agent": "engineer",
    "executor_agent": "engineer",
    "expert_agent": "expert",
    "judge_agent": "judge",
    "plan_prompt_template": "Plan {goal}",
    "execute_prompt_template": "Execute {plan}",
    "expert_prompt_template": "Expert {judge_bundle}",
    "judge_prompt_template": "Judge {judge_bundle}",
    "max_loops": 4,
    "max_runtime_minutes": 45,
    "max_judge_calls": 4
  },
  "agents": {
    "codex": {
      "id": "engineer",
      "provider": "codex",
      "role": "engineer",
      "model": "gpt-5.3-codex-spark"
    },
    "expert": {
      "id": "expert",
      "provider": "oracle",
      "role": "expert",
      "timeout_seconds": 3600
    },
    "judge": {
      "id": "judge",
      "provider": "codex",
      "role": "judge",
      "model": "gpt-5.4"
    }
  }
}
""",
        encoding="utf-8",
    )

    supervisor = WorkflowSupervisor(
        AppSettings(
            workspace_root=tmp_path,
            run_log_dir=tmp_path / ".shmocky" / "runs",
            codex_command="true",
            oracle_cli_command="true",
        )
    )

    recorded: dict[str, object] = {}

    async def fake_start_bridge(
        target_dir: Path,
        codex_agent: object,
        *,
        resume_thread_id: str | None = None,
        transcript_seed: list[TranscriptItem] | None = None,
    ) -> None:
        recorded["target_dir"] = str(target_dir)
        recorded["resume_thread_id"] = resume_thread_id
        recorded["transcript_seed_count"] = len(transcript_seed or [])
        recorded["codex_role"] = getattr(codex_agent, "role")

    async def fake_resume_from_oracle_checkpoint(context: LoadedRunContext) -> None:
        recorded["workflow_id"] = context.workflow.id
        recorded["expert_agent_id"] = context.expert_agent.id if context.expert_agent else None

    cast(Any, supervisor)._start_bridge = fake_start_bridge
    cast(Any, supervisor)._resume_from_oracle_checkpoint = fake_resume_from_oracle_checkpoint

    async def exercise() -> DashboardSnapshot:
        resumed = await supervisor.resume_run()
        if supervisor._run_task is not None:
            await supervisor._run_task
        return resumed

    resumed = asyncio.run(exercise())

    assert resumed.state.workflow_run is not None
    assert resumed.state.workflow_run.status == "running"
    assert recorded == {
        "target_dir": str(tmp_path / "repo"),
        "resume_thread_id": "thread-9",
        "transcript_seed_count": 1,
        "codex_role": "engineer",
        "workflow_id": "plan_execute_judge",
        "expert_agent_id": "expert",
    }


def test_supervisor_rolls_back_failed_run_start(tmp_path: Path) -> None:
    config_path = tmp_path / "shmocky.toml"
    config_path.write_text(
        """
[agents.engineer]
provider = "codex"
role = "engineer"

[agents.judge]
provider = "codex"
role = "judge"

[workflows.plan_execute_judge]
planner_agent = "engineer"
executor_agent = "engineer"
judge_agent = "judge"
""".strip(),
        encoding="utf-8",
    )
    target_dir = tmp_path.parent / f"{tmp_path.name}-target"
    target_dir.mkdir(parents=True, exist_ok=True)
    supervisor = WorkflowSupervisor(
        AppSettings(
            workspace_root=tmp_path,
            workflow_config_path=config_path,
            codex_command="true",
            oracle_cli_command="true",
        )
    )

    async def failing_start_bridge(target_dir: Path, codex_agent: object, **_: object) -> None:
        raise BridgeError("initialize failed")

    async def successful_start_bridge(target_dir: Path, codex_agent: object, **_: object) -> None:
        return None

    async def fake_execute_run(*args: object, **kwargs: object) -> None:
        await supervisor._finish_run(
            status="stopped",
            phase="stopped",
            note="test cleanup",
        )

    async def exercise() -> DashboardSnapshot:
        cast(Any, supervisor)._start_bridge = failing_start_bridge

        with pytest.raises(BridgeError, match="initialize failed"):
            await supervisor.start_run(
                WorkflowRunRequest(
                    workflow_id="plan_execute_judge",
                    target_dir=str(target_dir),
                    prompt="test startup rollback",
                )
            )

        assert supervisor._run_state is None
        assert supervisor._resources is None
        assert supervisor._archived_snapshot is None
        assert list(supervisor._recent_workflow_events) == []

        cast(Any, supervisor)._start_bridge = successful_start_bridge
        cast(Any, supervisor)._execute_run = fake_execute_run

        snapshot = await supervisor.start_run(
            WorkflowRunRequest(
                workflow_id="plan_execute_judge",
                target_dir=str(target_dir),
                prompt="test startup retry",
            )
        )
        await asyncio.sleep(0)
        return snapshot

    snapshot = asyncio.run(exercise())

    assert snapshot.state.workflow_run is not None
    assert snapshot.state.workflow_run.workflow_id == "plan_execute_judge"
    assert supervisor._run_state is not None
    assert supervisor._run_state.status == "stopped"
````

## File: README.md
````markdown
# Shmocky

Shmocky is a thin browser wrapper around `codex app-server`.

This repository is intentionally starting small. The current slice gives you a
single-user control surface with:

- a FastAPI backend that starts and manages one `codex app-server` subprocess
- append-only raw JSON-RPC event logs under `.shmocky/events/`
- a small in-memory projection for connection, thread, turn, transcript, and MCP status
- a Svelte 5 SPA that mirrors the live stream in a browser with a transcript pane and a raw event pane

## Current Scope

Implemented:

- backend startup and `initialize` handshake with `codex app-server`
- one active workflow run at a time, driven by repo-local TOML config
- one long-lived Codex thread per workflow run
- Oracle judging through a structured sidecar loop
- pause, resume, stop, and steer controls from the browser
- one-at-a-time Oracle consults through `POST /api/oracle/query`
- durable per-run history snapshots with transcript and workflow activity replay
- websocket fanout for browser observability
- file-backed raw event persistence before projection updates

Not implemented yet:

- general graph execution, multi-run scheduling, repo cloning, or browser-side workflow editing
- multi-thread management, resume, fork, archive, or notebook projections
- auth, budgets, policy gates, or multi-user tenancy

## Run

Backend:

```bash
uv sync --extra dev
uv run shmocky-api
```

Frontend:

```bash
npm --prefix apps/web install
npm --prefix apps/web run dev
```

If port `8000` is already in use, choose another backend port and point the Vite proxy at it:

```bash
SHMOCKY_API_PORT=8011 uv run shmocky-api
SHMOCKY_API_URL=http://127.0.0.1:8011 npm --prefix apps/web run dev
```

For headless or remote use through a hostname, also allow that hostname in Vite:

```bash
SHMOCKY_ALLOWED_HOSTS=lv426.yutani.tech npm --prefix apps/web run dev -- --host 0.0.0.0 --port 4321
```

The helper scripts in `scripts/` default to:

- backend on `127.0.0.1:${SHMOCKY_API_PORT:-8011}`
- frontend on `${SHMOCKY_FRONTEND_HOST:-0.0.0.0}:${SHMOCKY_FRONTEND_PORT:-4321}`
- Vite allowed hosts set from `SHMOCKY_ALLOWED_HOSTS` or, by default in `scripts/run-frontend.sh`, `*` for remote dev access

Then open the Vite URL in a browser. The header should show backend and Codex connectivity,
and the main workspace should let you select a workflow, point it at a local target directory,
launch a run, inspect Codex transcript plus workflow activity, pause, resume, stop, or steer,
respond to pending Codex approval or user-input requests from the workflow run tab, and durably
resume an Oracle-blocked paused run after a backend restart.

## Workflow Config

Shmocky reads workflow and agent definitions from `shmocky.toml` in the repo root.

The current built-in config ships one default workflow:

- `plan_execute_judge`

The current workflow shape is intentionally narrow:

- repo-local TOML config
- one active run at a time
- one Codex planner or executor thread per run
- one optional expert advisory hop plus a Codex judge that decides whether to continue
- target directories must be repository roots or standalone directories outside the Shmocky repo by default

Oracle agent definitions can also carry role-specific sidecar settings such as `remote_host`,
`chatgpt_url`, `timeout_seconds`, `model_strategy`, and `prompt_char_limit`, so different judge or
analyst roles can run with different budgets and dedicated ChatGPT project folders from the same
`shmocky.toml`.

If you switch Oracle’s browser model to slower modes such as ChatGPT Pro, raise or keep
`timeout_seconds` accordingly. The default backend fallback is now `3600` seconds, and Oracle-agent
failures inside workflow runs pause the run for operator intervention instead of failing it
immediately.

The backend exposes:

- `GET /api/workflows`
- `GET /api/runs`
- `GET /api/runs/{run_id}`
- `POST /api/runs`
- `GET /api/runs/active`
- `POST /api/runs/active/pause`
- `POST /api/runs/active/resume`
- `POST /api/runs/active/stop`
- `POST /api/runs/active/steer`
- `POST /api/server-requests/{request_id}/resolve`

The browser is the primary way to use these, but the endpoints are available for smoke tests and automation. Each run now stores a durable `dashboard-snapshot.json` under `.shmocky/runs/<run-id>/`, which the UI can reopen to restore transcript, workflow activity, and recent protocol context after the live Codex session has ended.

## Oracle Sidecar

Shmocky can also invoke a slow Oracle sidecar for high-value consultation work without folding it
into the Codex control loop. The backend reads:

- `ORACLE_REMOTE_TOKEN` from `.env`
- `ORACLE_REMOTE_HOST` optionally, defaulting to `https://oracle.yutani.tech:9473`

The backend normalizes URL-style remote hosts into the `host:port` format Oracle expects, so both
`https://oracle.yutani.tech:9473` and `oracle.yutani.tech:9473` work.

Query it directly through the API:

```bash
curl -X POST http://127.0.0.1:8000/api/oracle/query \
  -H 'content-type: application/json' \
  -d '{
    "agent_id": "judge",
    "prompt": "Review this architecture for hidden operational risks.",
    "files": ["README.md", "src/shmocky/**/*.py"]
  }'
```

Notes:

- Oracle calls are serialized intentionally to avoid spamming the remote signed-in browser.
- The current slice returns the final answer only. It does not stream partial Oracle output into the UI.
- Attached `files` are resolved relative to the workspace root and expanded from glob patterns before invocation.
- Oracle prompt size is bounded by the selected Oracle agent's `prompt_char_limit` when `agent_id` is
  provided, otherwise it falls back to `SHMOCKY_ORACLE_PROMPT_CHAR_LIMIT` and defaults to `20000`.

## Quality Gates

```bash
uv sync --extra dev
npm --prefix apps/web install
uv run ruff check .
uv run ty check
uv run --extra dev pytest -q
npm --prefix apps/web run check
npm --prefix apps/web run biome:check
```

## Notes

- Raw app-server traffic is treated as sensitive operational data. Do not commit `.shmocky/`.
- The browser surface is intentionally observability-first, not a general orchestration layer.
- The relevant design record for this slice is [plans/001-browser-mirror.md](/nvme/development/shmocky/plans/001-browser-mirror.md).
````

## File: apps/web/src/routes/+page.svelte
````svelte
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
						<div class="text-muted-foreground">Codex model</div>
						<div class="truncate">{viewedState()?.thread?.model ?? "—"}</div>
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
````

## File: src/shmocky/supervisor.py
````python
from __future__ import annotations

import asyncio
import contextlib
import json
import re
import subprocess
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from fastapi import HTTPException
from pydantic import ValidationError

from .bridge import BridgeError, CodexAppServerBridge
from .event_store import WorkflowEventStore
from .models import (
    AgentDefinition,
    CodexAgentConfig,
    ConnectionState,
    DashboardSnapshot,
    DashboardState,
    JudgeDecision,
    OracleQueryRequest,
    OracleResumeCheckpoint,
    RunHistoryEntry,
    RunHistoryResponse,
    ServerRequestResolutionRequest,
    StreamEnvelope,
    TranscriptItem,
    WorkflowCatalogResponse,
    WorkflowDefinition,
    WorkflowEventRecord,
    WorkflowPhase,
    WorkflowRunRequest,
    WorkflowRunState,
    WorkflowRunStatus,
    WorkflowSteerRequest,
)
from .oracle_agent import OracleAgent, OracleAgentError, OracleNotConfiguredError
from .settings import AppSettings
from .workflow_config import WorkflowConfigError, WorkflowConfigLoader


class WorkflowSupervisorError(RuntimeError):
    pass


class WorkflowConflictError(WorkflowSupervisorError):
    pass


class WorkflowNotFoundError(WorkflowSupervisorError):
    pass


class WorkflowStoppedError(WorkflowSupervisorError):
    pass


@dataclass(slots=True)
class RunResources:
    run_dir: Path
    workflow_event_store: WorkflowEventStore


@dataclass(slots=True)
class LoadedRunContext:
    workflow: WorkflowDefinition
    codex_agent: AgentDefinition
    expert_agent: AgentDefinition | None
    judge_agent: AgentDefinition


class WorkflowSupervisor:
    RUN_MANIFEST_FILENAME = "run.json"
    RUN_SNAPSHOT_FILENAME = "dashboard-snapshot.json"
    SNAPSHOT_FLUSH_DEBOUNCE_SECONDS = 0.25

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._loader = WorkflowConfigLoader(settings)
        self._oracle = OracleAgent(settings)
        self._lock = asyncio.Lock()
        self._subscribers: set[asyncio.Queue[StreamEnvelope]] = set()
        self._recent_workflow_events: deque[WorkflowEventRecord] = deque(maxlen=200)
        self._run_state: WorkflowRunState | None = None
        self._run_task: asyncio.Task[None] | None = None
        self._bridge: CodexAppServerBridge | None = None
        self._bridge_task: asyncio.Task[None] | None = None
        self._bridge_queue: asyncio.Queue[StreamEnvelope] | None = None
        self._resources: RunResources | None = None
        self._archived_snapshot: DashboardSnapshot | None = None
        self._snapshot_flush_task: asyncio.Task[None] | None = None
        self._snapshot_flush_lock = asyncio.Lock()
        self._staged_snapshot: DashboardSnapshot | None = None
        self._staged_snapshot_path: Path | None = None
        self._staged_snapshot_revision = 0
        self._snapshot_revision = 0
        self._snapshot_flushed_revision = 0
        self._pause_gate = asyncio.Event()
        self._pause_gate.set()
        self._last_catalog_error: str | None = None
        self._restore_resumable_run()

    def _restore_resumable_run(self) -> None:
        run_dir = self._find_resumable_run_dir()
        if run_dir is None:
            return
        snapshot_path = run_dir / self.RUN_SNAPSHOT_FILENAME
        try:
            snapshot = DashboardSnapshot.model_validate_json(
                snapshot_path.read_text(encoding="utf-8")
            )
        except Exception:
            return
        workflow_run = snapshot.state.workflow_run
        if (
            workflow_run is None
            or workflow_run.status != "paused"
            or workflow_run.oracle_resume_checkpoint is None
        ):
            return
        self._run_state = workflow_run
        self._resources = RunResources(
            run_dir=run_dir,
            workflow_event_store=WorkflowEventStore(run_dir / "workflow-events.jsonl"),
        )
        self._recent_workflow_events.clear()
        self._recent_workflow_events.extend(
            self._load_workflow_events(run_dir / "workflow-events.jsonl")
        )
        self._archived_snapshot = snapshot
        self._pause_gate.clear()

    def _find_resumable_run_dir(self) -> Path | None:
        for run_dir in sorted(
            self._settings.run_log_dir.glob("*"),
            key=lambda path: path.name,
            reverse=True,
        ):
            if not run_dir.is_dir():
                continue
            snapshot_path = run_dir / self.RUN_SNAPSHOT_FILENAME
            if not snapshot_path.exists():
                continue
            try:
                snapshot = DashboardSnapshot.model_validate_json(
                    snapshot_path.read_text(encoding="utf-8")
                )
            except Exception:
                continue
            workflow_run = snapshot.state.workflow_run
            if (
                workflow_run is not None
                and workflow_run.status == "paused"
                and workflow_run.oracle_resume_checkpoint is not None
            ):
                return run_dir
        return None

    @staticmethod
    def _load_workflow_events(path: Path) -> list[WorkflowEventRecord]:
        if not path.exists():
            return []
        records: list[WorkflowEventRecord] = []
        try:
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    try:
                        records.append(WorkflowEventRecord.model_validate_json(line))
                    except Exception:
                        continue
        except OSError:
            return []
        return records[-200:]

    def _load_run_context_from_manifest(self) -> LoadedRunContext:
        if self._resources is None:
            raise WorkflowSupervisorError("No workflow resources are available.")
        manifest_path = self._resources.run_dir / self.RUN_MANIFEST_FILENAME
        if not manifest_path.exists():
            raise WorkflowSupervisorError(
                f"Run manifest is missing for '{self._resources.run_dir.name}'."
            )
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            workflow = WorkflowDefinition.model_validate(payload["workflow"])
            agents_payload = payload["agents"]
            codex_agent = AgentDefinition.model_validate(agents_payload["codex"])
            expert_payload = agents_payload.get("expert")
            expert_agent = (
                AgentDefinition.model_validate(expert_payload)
                if isinstance(expert_payload, dict)
                else None
            )
            judge_agent = AgentDefinition.model_validate(agents_payload["judge"])
        except Exception as exc:
            raise WorkflowSupervisorError(
                f"Run manifest for '{self._resources.run_dir.name}' is unreadable."
            ) from exc
        return LoadedRunContext(
            workflow=workflow,
            codex_agent=codex_agent,
            expert_agent=expert_agent,
            judge_agent=judge_agent,
        )

    def snapshot(self) -> DashboardSnapshot:
        if self._bridge is None and self._archived_snapshot is not None:
            snapshot = self._archived_snapshot.model_copy(deep=True)
            snapshot.state.connection.backend_online = True
            snapshot.state.connection.codex_connected = False
            snapshot.state.connection.initialized = False
            snapshot.state.connection.app_server_pid = None
            snapshot.state.pending_server_request = None
            if self._run_state is not None:
                snapshot.state.workflow_run = self._run_state.model_copy(deep=True)
            return snapshot

        bridge_snapshot = self._bridge.snapshot() if self._bridge is not None else None
        bridge_state = bridge_snapshot.state if bridge_snapshot is not None else None
        workspace_root = (
            bridge_state.workspace_root if bridge_state is not None else str(self._settings.workspace_root)
        )
        event_log_path = (
            bridge_state.event_log_path
            if bridge_state is not None
            else str(self._settings.event_log_dir)
        )
        state = DashboardState(
            workspace_root=workspace_root,
            event_log_path=event_log_path,
            connection=(
                bridge_state.connection.model_copy(deep=True)
                if bridge_state is not None
                else ConnectionState()
            ),
            thread=bridge_state.thread.model_copy(deep=True) if bridge_state and bridge_state.thread else None,
            turn=bridge_state.turn.model_copy(deep=True) if bridge_state and bridge_state.turn else None,
            transcript=(
                [item.model_copy(deep=True) for item in bridge_state.transcript]
                if bridge_state is not None
                else []
            ),
            mcp_servers=dict(bridge_state.mcp_servers) if bridge_state is not None else {},
            rate_limits=bridge_state.rate_limits if bridge_state is not None else None,
            pending_server_request=(
                bridge_state.pending_server_request.model_copy(deep=True)
                if bridge_state and bridge_state.pending_server_request
                else None
            ),
            workflow_run=self._run_state.model_copy(deep=True) if self._run_state is not None else None,
        )
        return DashboardSnapshot(
            state=state,
            recent_events=bridge_snapshot.recent_events if bridge_snapshot is not None else [],
            recent_workflow_events=[
                record.model_copy(deep=True) for record in self._recent_workflow_events
            ],
        )

    def runs_history(self) -> RunHistoryResponse:
        run_entries: list[RunHistoryEntry] = []
        for run_dir in sorted(
            self._settings.run_log_dir.glob("*"),
            key=lambda path: path.name,
            reverse=True,
        ):
            if not run_dir.is_dir():
                continue
            snapshot_path = run_dir / self.RUN_SNAPSHOT_FILENAME
            if not snapshot_path.exists():
                continue
            try:
                snapshot = DashboardSnapshot.model_validate_json(
                    snapshot_path.read_text(encoding="utf-8")
                )
            except Exception:
                continue
            workflow_run = snapshot.state.workflow_run
            if workflow_run is None:
                continue
            run_entries.append(
                RunHistoryEntry(
                    id=workflow_run.id,
                    run_name=workflow_run.run_name,
                    workflow_id=workflow_run.workflow_id,
                    target_dir=workflow_run.target_dir,
                    status=workflow_run.status,
                    phase=workflow_run.phase,
                    started_at=workflow_run.started_at,
                    updated_at=workflow_run.updated_at,
                    completed_at=workflow_run.completed_at,
                    last_judge_decision=workflow_run.last_judge_decision,
                    last_judge_summary=workflow_run.last_judge_summary,
                    last_error=workflow_run.last_error,
                )
            )
        return RunHistoryResponse(runs=run_entries)

    def load_run_snapshot(self, run_id: str) -> DashboardSnapshot:
        snapshot_path = self._settings.run_log_dir / run_id / self.RUN_SNAPSHOT_FILENAME
        if not snapshot_path.exists():
            raise WorkflowNotFoundError(f"Unknown run '{run_id}'.")
        try:
            return DashboardSnapshot.model_validate_json(
                snapshot_path.read_text(encoding="utf-8")
            )
        except Exception as exc:
            raise WorkflowSupervisorError(
                f"Stored snapshot for run '{run_id}' is unreadable."
            ) from exc

    def workflows_catalog(self) -> WorkflowCatalogResponse:
        try:
            catalog = self._loader.load()
            self._last_catalog_error = None
            return catalog
        except WorkflowConfigError as exc:
            self._last_catalog_error = str(exc)
            return WorkflowCatalogResponse(
                config_path=str(self._loader.path),
                loaded=False,
                error=str(exc),
            )

    async def subscribe(self) -> asyncio.Queue[StreamEnvelope]:
        queue: asyncio.Queue[StreamEnvelope] = asyncio.Queue(maxsize=512)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[StreamEnvelope]) -> None:
        self._subscribers.discard(queue)

    async def shutdown(self) -> None:
        async with self._lock:
            if self._run_task is not None:
                self._run_task.cancel()
                try:
                    await self._run_task
                except asyncio.CancelledError:
                    pass
                self._run_task = None
            await self._stop_bridge()
            if (
                self._run_state is not None
                and self._run_state.status == "paused"
                and self._run_state.oracle_resume_checkpoint is not None
            ):
                self._stage_run_snapshot()
            await self._flush_staged_snapshot_now()

    async def start_thread(self) -> DashboardSnapshot:
        if self._bridge is None:
            raise WorkflowSupervisorError("No active Codex session. Start a workflow run first.")
        return await self._bridge.ensure_thread()

    async def send_prompt(self, prompt: str) -> DashboardSnapshot:
        if self._bridge is None:
            raise WorkflowSupervisorError("No active Codex session. Start a workflow run first.")
        return await self._bridge.start_turn(prompt)

    async def interrupt_turn(self) -> DashboardSnapshot:
        if self._bridge is None:
            raise WorkflowSupervisorError("No active Codex session. Start a workflow run first.")
        return await self._bridge.interrupt_turn()

    async def resolve_server_request(
        self,
        request_id: str,
        payload: ServerRequestResolutionRequest,
    ) -> DashboardSnapshot:
        if self._bridge is None:
            raise WorkflowSupervisorError("No active Codex session. Start a workflow run first.")
        pending = self._bridge.snapshot().state.pending_server_request
        if pending is None:
            raise WorkflowSupervisorError("There is no pending server request to resolve.")
        if pending.request_id != request_id:
            raise WorkflowSupervisorError(
                f"Pending server request is '{pending.request_id}', not '{request_id}'."
            )
        await self._bridge.resolve_server_request(request_id, result=payload.result)
        await self._record_workflow_event(
            "server_request_responded",
            f"Operator responded to {pending.method}.",
            payload={"requestId": request_id, "method": pending.method},
        )
        return self.snapshot()

    async def start_run(self, payload: WorkflowRunRequest) -> DashboardSnapshot:
        async with self._lock:
            if self._run_state is not None and self._run_state.status in {
                "starting",
                "running",
                "paused",
            }:
                raise WorkflowConflictError("A workflow run is already active.")

            catalog = self._loader.load()
            workflow = next(
                (entry for entry in catalog.workflows if entry.id == payload.workflow_id),
                None,
            )
            if workflow is None:
                raise WorkflowNotFoundError(f"Unknown workflow '{payload.workflow_id}'.")

            target_dir = self._validate_target_dir(Path(payload.target_dir))

            agent_by_id = {agent.id: agent for agent in catalog.agents}
            codex_agent = agent_by_id[workflow.executor_agent]
            expert_agent = (
                agent_by_id[workflow.expert_agent]
                if workflow.expert_agent is not None
                else None
            )
            judge_agent = agent_by_id[workflow.judge_agent]

            run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
            run_dir = self._settings.run_log_dir / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            resources = RunResources(
                run_dir=run_dir,
                workflow_event_store=WorkflowEventStore(run_dir / "workflow-events.jsonl"),
            )
            self._resources = resources
            self._archived_snapshot = None
            self._recent_workflow_events.clear()
            self._pause_gate.set()
            self._run_state = WorkflowRunState(
                id=run_id,
                run_name=payload.run_name.strip() if payload.run_name else None,
                workflow_id=workflow.id,
                target_dir=str(target_dir),
                goal=payload.prompt,
                status="starting",
                phase="idle",
                codex_agent_id=codex_agent.id,
                expert_agent_id=expert_agent.id if expert_agent is not None else None,
                judge_agent_id=judge_agent.id,
                started_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                max_loops=workflow.max_loops,
                max_judge_calls=workflow.max_judge_calls,
                max_runtime_minutes=workflow.max_runtime_minutes,
            )
            self._write_json(
                run_dir / self.RUN_MANIFEST_FILENAME,
                {
                    "runId": run_id,
                    "request": payload.model_dump(mode="json"),
                    "workflow": workflow.model_dump(mode="json"),
                    "agents": {
                        "codex": codex_agent.model_dump(mode="json"),
                        "expert": (
                            expert_agent.model_dump(mode="json")
                            if expert_agent is not None
                            else None
                        ),
                        "judge": judge_agent.model_dump(mode="json"),
                    },
                },
            )
            self._stage_run_snapshot()
            await self._flush_staged_snapshot_now()
            try:
                await self._record_workflow_event(
                    "run_started",
                    (
                        f"Started run '{self._run_state.run_name}' using workflow '{workflow.id}' for {target_dir}"
                        if self._run_state.run_name
                        else f"Started workflow '{workflow.id}' for {target_dir}"
                    ),
                    payload={
                        "runId": run_id,
                        "runName": self._run_state.run_name,
                        "workflowId": workflow.id,
                        "targetDir": str(target_dir),
                    },
                )
                await self._start_bridge(target_dir, codex_agent)
            except Exception:
                await self._rollback_failed_run_start()
                raise
            self._run_task = asyncio.create_task(
                self._execute_run(workflow, codex_agent, expert_agent, judge_agent)
            )
            await self._broadcast_state()
            return self.snapshot()

    async def _rollback_failed_run_start(self) -> None:
        await self._stop_bridge()
        if self._run_task is not None:
            self._run_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._run_task
            self._run_task = None
        await self._cancel_snapshot_flush_task()
        self._run_state = None
        self._resources = None
        self._archived_snapshot = None
        self._staged_snapshot = None
        self._staged_snapshot_path = None
        self._staged_snapshot_revision = 0
        self._snapshot_revision = 0
        self._snapshot_flushed_revision = 0
        self._recent_workflow_events.clear()
        self._pause_gate.set()

    def _validate_target_dir(self, target_dir: Path) -> Path:
        resolved = target_dir.expanduser().resolve()
        if not resolved.exists() or not resolved.is_dir():
            raise WorkflowSupervisorError(
                f"Target directory does not exist or is not a directory: {resolved}"
            )
        if not self._settings.allow_nested_target_dirs and resolved.is_relative_to(
            self._settings.workspace_root
        ):
            raise WorkflowSupervisorError(
                "Target directory is inside the Shmocky workspace. "
                "Use a repository root or an external directory for isolation."
            )

        containing_git_root = self._git_root_for(resolved)
        if (
            not self._settings.allow_nested_target_dirs
            and containing_git_root is not None
            and containing_git_root != resolved
        ):
            raise WorkflowSupervisorError(
                "Target directory is nested inside another git repository: "
                f"{containing_git_root}. Use the repository root itself so parent repo "
                "instructions and history do not leak into the run."
            )
        return resolved

    async def pause_run(self) -> DashboardSnapshot:
        async with self._lock:
            if self._run_state is None:
                raise WorkflowSupervisorError("No workflow run exists.")
            if self._run_state.status in {"completed", "failed", "stopped"}:
                return self.snapshot()
            self._run_state.pause_requested = True
            self._run_state.updated_at = datetime.now(UTC)
            await self._record_workflow_event(
                "pause_requested",
                "Pause requested; the run will pause after the current step.",
            )
            return self.snapshot()

    async def resume_run(self) -> DashboardSnapshot:
        async with self._lock:
            if self._run_state is None:
                raise WorkflowSupervisorError("No workflow run exists.")
            self._run_state.pause_requested = False
            if self._run_state.status == "paused":
                if self._run_task is None:
                    checkpoint = self._run_state.oracle_resume_checkpoint
                    if checkpoint is None:
                        raise WorkflowSupervisorError(
                            "This paused run cannot be resumed after backend restart."
                        )
                    context = self._load_run_context_from_manifest()
                    transcript_seed = (
                        self._archived_snapshot.state.transcript
                        if self._archived_snapshot is not None
                        else []
                    )
                    await self._start_bridge(
                        Path(self._run_state.target_dir),
                        context.codex_agent,
                        resume_thread_id=checkpoint.thread_id,
                        transcript_seed=transcript_seed,
                    )
                    self._run_task = asyncio.create_task(
                        self._resume_from_oracle_checkpoint(context)
                    )
                self._run_state.status = "running"
                self._run_state.updated_at = datetime.now(UTC)
                self._pause_gate.set()
                await self._record_workflow_event("resumed", "Workflow run resumed.")
            return self.snapshot()

    async def stop_run(self) -> DashboardSnapshot:
        async with self._lock:
            if self._run_state is None:
                raise WorkflowSupervisorError("No workflow run exists.")
            self._run_state.stop_requested = True
            self._run_state.updated_at = datetime.now(UTC)
            self._pause_gate.set()
            if self._bridge is not None:
                await self._bridge.interrupt_turn()
            await self._record_workflow_event(
                "stop_requested",
                "Stop requested; the run will stop after the current step.",
            )
            return self.snapshot()

    async def steer_run(self, payload: WorkflowSteerRequest) -> DashboardSnapshot:
        async with self._lock:
            if self._run_state is None:
                raise WorkflowSupervisorError("No workflow run exists.")
            self._run_state.pending_steering_notes.append(payload.note.strip())
            self._run_state.updated_at = datetime.now(UTC)
            await self._record_workflow_event(
                "steer_queued",
                "Queued an operator steering note for the next Codex execution turn.",
                payload={"note": payload.note.strip()},
            )
            return self.snapshot()

    async def _start_bridge(
        self,
        target_dir: Path,
        codex_agent: Any,
        *,
        resume_thread_id: str | None = None,
        transcript_seed: list[TranscriptItem] | None = None,
    ) -> None:
        await self._stop_bridge()
        bridge = CodexAppServerBridge(
            self._settings,
            workspace_root=target_dir,
            event_log_dir=(self._resources.run_dir / "codex-events") if self._resources else None,
            agent_config=CodexAgentConfig(
                role=codex_agent.role,
                startup_prompt=codex_agent.startup_prompt,
                description=codex_agent.description,
                model=codex_agent.model,
                model_provider=codex_agent.model_provider,
                reasoning_effort=codex_agent.reasoning_effort,
                approval_policy=codex_agent.approval_policy or "never",
                sandbox_mode=codex_agent.sandbox_mode or "workspace-write",
                web_access=codex_agent.web_access or "disabled",
                service_tier=codex_agent.service_tier,
            ),
        )
        await bridge.start()
        if resume_thread_id is not None:
            await bridge.resume_thread(resume_thread_id)
        if transcript_seed:
            bridge.seed_transcript(transcript_seed)
        queue = await bridge.subscribe()
        self._bridge = bridge
        self._bridge_queue = queue
        self._bridge_task = asyncio.create_task(self._relay_bridge_events(queue))
        await self._record_workflow_event(
            "codex_session_resumed" if resume_thread_id is not None else "codex_session_started",
            (
                "Resumed Codex app-server session for the workflow run."
                if resume_thread_id is not None
                else "Started Codex app-server session for the workflow run."
            ),
            payload={
                "workspaceRoot": str(target_dir),
                "threadId": resume_thread_id,
            },
        )

    async def _stop_bridge(self) -> None:
        if self._bridge_task is not None:
            self._bridge_task.cancel()
            try:
                await self._bridge_task
            except asyncio.CancelledError:
                pass
            self._bridge_task = None
        if self._bridge is not None and self._bridge_queue is not None:
            self._bridge.unsubscribe(self._bridge_queue)
        if self._bridge is not None:
            await self._bridge.stop()
        self._bridge = None
        self._bridge_queue = None

    async def _relay_bridge_events(self, queue: asyncio.Queue[StreamEnvelope]) -> None:
        try:
            while True:
                envelope = await queue.get()
                if envelope.type != "event" or envelope.event is None:
                    continue
                self._stage_run_snapshot()
                await self._broadcast(
                    StreamEnvelope(
                        type="event",
                        state=self.snapshot().state,
                        event=envelope.event,
                        workflow_event=None,
                    )
                )
        except asyncio.CancelledError:
            return

    async def _execute_run(
        self,
        workflow: Any,
        codex_agent: Any,
        expert_agent: Any,
        judge_agent: Any,
    ) -> None:
        try:
            await self._ensure_checkpoint("planning", "Planning with Codex.")
            plan_prompt = self._render_template(
                workflow.plan_prompt_template,
                goal=self._run_state.goal if self._run_state else "",
            )
            plan_output = await self._run_codex_turn(plan_prompt, kind="planning")
            if self._run_state is None:
                raise WorkflowSupervisorError("Workflow run disappeared during planning.")
            self._run_state.last_plan = self._clip(plan_output)
            initial_execute_prompt = self._render_template(
                workflow.execute_prompt_template,
                goal=self._run_state.goal,
                plan=plan_output,
            )
            await self._execute_remaining_loops(
                workflow,
                plan_output,
                initial_execute_prompt,
                start_loop=1,
                expert_agent=expert_agent,
                judge_agent=judge_agent,
            )
        except WorkflowStoppedError:
            await self._finish_run(
                status="stopped",
                phase="stopped",
                note="Workflow run stopped by operator request.",
            )
        except (BridgeError, OracleAgentError, OracleNotConfiguredError, WorkflowSupervisorError) as exc:
            await self._finish_run(status="failed", phase="failed", note=str(exc))
        except Exception as exc:  # pragma: no cover - defensive path
            await self._finish_run(status="failed", phase="failed", note=str(exc))

    async def _resume_from_oracle_checkpoint(self, context: LoadedRunContext) -> None:
        try:
            if self._run_state is None:
                raise WorkflowSupervisorError("No workflow run exists.")
            checkpoint = self._run_state.oracle_resume_checkpoint
            if checkpoint is None:
                raise WorkflowSupervisorError("No Oracle resume checkpoint is available.")
            if self._run_state.last_codex_output is None:
                raise WorkflowSupervisorError(
                    "Cannot resume Oracle-blocked run without preserved Codex output."
                )
            loop_index = checkpoint.loop_index
            plan_output = self._run_state.last_plan or ""
            codex_output = self._run_state.last_codex_output
            expert_assessment = self._run_state.last_expert_assessment

            if checkpoint.agent_label == "expert":
                expert_agent = context.expert_agent
                if expert_agent is None or context.workflow.expert_prompt_template is None:
                    raise WorkflowSupervisorError(
                        "Cannot resume expert step because the expert agent is missing."
                    )
                await self._ensure_checkpoint(
                    "advising",
                    f"Resuming expert assessment loop {loop_index}.",
                )
                while True:
                    try:
                        expert_assessment = await self._run_expert(expert_agent, checkpoint.prompt)
                        break
                    except (OracleAgentError, OracleNotConfiguredError) as exc:
                        if expert_agent.provider != "oracle":
                            raise
                        await self._pause_for_oracle_failure(
                            agent_label="expert",
                            agent_id=expert_agent.id,
                            prompt=checkpoint.prompt,
                            detail=str(exc),
                        )
                if self._run_state is None:
                    raise WorkflowSupervisorError(
                        "Workflow run disappeared during expert assessment."
                    )
                self._clear_oracle_pause("expert")
                self._run_state.last_expert_assessment = self._clip(
                    expert_assessment,
                    limit=8_000,
                )
                await self._ensure_checkpoint("judging", f"Judge evaluation loop {loop_index}.")
                await self._check_budgets(loop_index, before_judge=True)
                judge_bundle = await self._build_judge_bundle(
                    codex_output,
                    expert_assessment=expert_assessment,
                )
                judge_prompt = self._render_agent_prompt(
                    context.workflow.judge_prompt_template,
                    agent=context.judge_agent,
                    goal=self._run_state.goal or "",
                    plan=plan_output,
                    last_output=codex_output,
                    judge_bundle=judge_bundle,
                    expert_assessment=expert_assessment or "",
                )
            else:
                await self._ensure_checkpoint(
                    "judging",
                    f"Resuming judge evaluation loop {loop_index}.",
                )
                await self._check_budgets(loop_index, before_judge=True)
                judge_prompt = checkpoint.prompt

            while True:
                try:
                    decision = await self._run_judge(context.judge_agent, judge_prompt)
                    break
                except (OracleAgentError, OracleNotConfiguredError) as exc:
                    if context.judge_agent.provider != "oracle":
                        raise
                    await self._pause_for_oracle_failure(
                        agent_label="judge",
                        agent_id=context.judge_agent.id,
                        prompt=judge_prompt,
                        detail=str(exc),
                    )
            if self._run_state is None:
                raise WorkflowSupervisorError("Workflow run disappeared after judging.")
            self._clear_oracle_pause("judge")
            next_prompt = await self._apply_judge_decision(decision)
            if next_prompt is None:
                return
            await self._execute_remaining_loops(
                context.workflow,
                plan_output,
                next_prompt,
                start_loop=loop_index + 1,
                expert_agent=context.expert_agent,
                judge_agent=context.judge_agent,
            )
        except WorkflowStoppedError:
            await self._finish_run(
                status="stopped",
                phase="stopped",
                note="Workflow run stopped by operator request.",
            )
        except (BridgeError, OracleAgentError, OracleNotConfiguredError, WorkflowSupervisorError) as exc:
            await self._finish_run(status="failed", phase="failed", note=str(exc))
        except Exception as exc:  # pragma: no cover - defensive path
            await self._finish_run(status="failed", phase="failed", note=str(exc))

    async def _execute_remaining_loops(
        self,
        workflow: Any,
        plan_output: str,
        execute_prompt: str,
        *,
        start_loop: int,
        expert_agent: Any,
        judge_agent: Any,
    ) -> None:
        loop_index = start_loop - 1
        while True:
            loop_index += 1
            await self._check_budgets(loop_index)
            if self._run_state is None:
                raise WorkflowSupervisorError("Workflow run disappeared during execution.")
            self._run_state.current_loop = loop_index
            self._run_state.updated_at = datetime.now(UTC)

            await self._ensure_checkpoint("executing", f"Codex execution loop {loop_index}.")
            execute_prompt = self._consume_steering(execute_prompt)
            codex_output = await self._run_codex_turn(execute_prompt, kind="executing")
            if self._run_state is None:
                raise WorkflowSupervisorError("Workflow run disappeared during judging.")
            self._run_state.last_codex_output = self._clip(codex_output)

            expert_assessment: str | None = None
            if expert_agent is not None and workflow.expert_prompt_template is not None:
                await self._ensure_checkpoint(
                    "advising",
                    f"Expert assessment loop {loop_index}.",
                )
                expert_bundle = await self._build_judge_bundle(
                    codex_output,
                    expert_assessment=None,
                )
                expert_prompt = self._render_agent_prompt(
                    workflow.expert_prompt_template,
                    agent=expert_agent,
                    goal=self._run_state.goal or "",
                    plan=plan_output,
                    last_output=codex_output,
                    judge_bundle=expert_bundle,
                    expert_assessment="",
                )
                while True:
                    try:
                        expert_assessment = await self._run_expert(expert_agent, expert_prompt)
                        break
                    except (OracleAgentError, OracleNotConfiguredError) as exc:
                        if expert_agent.provider != "oracle":
                            raise
                        await self._pause_for_oracle_failure(
                            agent_label="expert",
                            agent_id=expert_agent.id,
                            prompt=expert_prompt,
                            detail=str(exc),
                        )
                if self._run_state is None:
                    raise WorkflowSupervisorError(
                        "Workflow run disappeared during expert assessment."
                    )
                self._clear_oracle_pause("expert")
                self._run_state.last_expert_assessment = self._clip(
                    expert_assessment,
                    limit=8_000,
                )

            await self._ensure_checkpoint("judging", f"Judge evaluation loop {loop_index}.")
            await self._check_budgets(loop_index, before_judge=True)
            judge_bundle = await self._build_judge_bundle(
                codex_output,
                expert_assessment=expert_assessment,
            )
            judge_prompt = self._render_agent_prompt(
                workflow.judge_prompt_template,
                agent=judge_agent,
                goal=self._run_state.goal or "",
                plan=plan_output,
                last_output=codex_output,
                judge_bundle=judge_bundle,
                expert_assessment=expert_assessment or "",
            )
            while True:
                try:
                    decision = await self._run_judge(judge_agent, judge_prompt)
                    break
                except (OracleAgentError, OracleNotConfiguredError) as exc:
                    if judge_agent.provider != "oracle":
                        raise
                    await self._pause_for_oracle_failure(
                        agent_label="judge",
                        agent_id=judge_agent.id,
                        prompt=judge_prompt,
                        detail=str(exc),
                    )
            if self._run_state is None:
                raise WorkflowSupervisorError("Workflow run disappeared after judging.")
            self._clear_oracle_pause("judge")
            next_prompt = await self._apply_judge_decision(decision)
            if next_prompt is None:
                return
            execute_prompt = next_prompt

    async def _apply_judge_decision(self, decision: JudgeDecision) -> str | None:
        if self._run_state is None:
            raise WorkflowSupervisorError("Workflow run disappeared after judging.")
        self._run_state.judge_calls += 1
        self._run_state.last_judge_decision = decision.decision
        self._run_state.last_judge_summary = decision.summary
        self._run_state.last_continuation_prompt = (
            decision.next_prompt if decision.decision == "continue" else None
        )
        self._run_state.updated_at = datetime.now(UTC)

        if decision.decision == "complete":
            await self._finish_run(
                status="completed",
                phase="completed",
                note=decision.completion_note or decision.summary,
            )
            return None
        if decision.decision == "fail":
            await self._finish_run(
                status="failed",
                phase="failed",
                note=decision.failure_reason or decision.summary,
            )
            return None
        if not decision.next_prompt:
            raise WorkflowSupervisorError(
                "Judge returned continue without a next_prompt."
            )
        return decision.next_prompt

    async def _run_codex_turn(self, prompt: str, *, kind: str) -> str:
        if self._bridge is None:
            raise WorkflowSupervisorError("Codex session is not available.")
        await self._record_workflow_event(
            "codex_turn_started",
            f"Started Codex {kind} turn.",
            payload={"prompt": self._clip(prompt, limit=2_000)},
        )
        snapshot = await self._bridge.start_turn(prompt)
        turn = snapshot.state.turn
        if turn is None:
            raise WorkflowSupervisorError("Codex did not create a turn.")
        completed = await self._bridge.wait_for_turn_completion(turn.id)
        assistant_text = self._assistant_text_for_turn(completed, turn.id)
        await self._record_workflow_event(
            "codex_turn_completed",
            f"Completed Codex {kind} turn.",
            payload={
                "turnId": turn.id,
                "status": completed.state.turn.status if completed.state.turn else None,
            },
        )
        if completed.state.turn and completed.state.turn.error:
            raise WorkflowSupervisorError(completed.state.turn.error)
        if not assistant_text:
            raise WorkflowSupervisorError("Codex completed the turn without an assistant message.")
        return assistant_text

    async def _run_expert(self, expert_agent: Any, prompt: str) -> str:
        if self._resources is not None:
            self._write_json(self._resources.run_dir / "last-expert-request.json", {"prompt": prompt})
        await self._record_workflow_event(
            "expert_started",
            f"Started {expert_agent.provider} expert assessment.",
            payload={"agentId": expert_agent.id, "provider": expert_agent.provider},
        )
        if expert_agent.provider == "oracle":
            response = await self._oracle.query(
                OracleQueryRequest(prompt=prompt),
                remote_host=expert_agent.remote_host,
                chatgpt_url=expert_agent.chatgpt_url,
                model_strategy=expert_agent.model_strategy,
                timeout_seconds=expert_agent.timeout_seconds,
                prompt_char_limit=expert_agent.prompt_char_limit,
            )
            answer = response.answer.strip()
            if self._resources is not None:
                self._write_json(
                    self._resources.run_dir / "last-expert-response.json",
                    {
                        "answer": answer,
                        "provider": "oracle",
                        "remoteHost": response.remote_host,
                        "durationSeconds": response.duration_seconds,
                    },
                )
        else:
            answer = await self._run_aux_codex_turn(
                expert_agent,
                prompt,
                event_log_subdir="expert-codex-events",
                label="expert",
            )
            if self._resources is not None:
                self._write_json(
                    self._resources.run_dir / "last-expert-response.json",
                    {
                        "answer": answer,
                        "provider": "codex",
                    },
                )
        await self._record_workflow_event(
            "expert_completed",
            f"Completed {expert_agent.provider} expert assessment.",
            payload={
                "agentId": expert_agent.id,
                "provider": expert_agent.provider,
                "answer": self._clip(answer, limit=2_000),
            },
        )
        return answer

    async def _run_judge(self, judge_agent: Any, prompt: str) -> JudgeDecision:
        if self._resources is not None:
            self._write_json(self._resources.run_dir / "last-judge-request.json", {"prompt": prompt})
        await self._record_workflow_event(
            "judge_started",
            f"Started {judge_agent.provider} judge evaluation.",
            payload={"agentId": judge_agent.id, "provider": judge_agent.provider},
        )
        if judge_agent.provider == "oracle":
            response = await self._oracle.query(
                OracleQueryRequest(prompt=prompt),
                remote_host=judge_agent.remote_host,
                chatgpt_url=judge_agent.chatgpt_url,
                model_strategy=judge_agent.model_strategy,
                timeout_seconds=judge_agent.timeout_seconds,
                prompt_char_limit=judge_agent.prompt_char_limit,
            )
            raw_answer = response.answer.strip()
            response_payload: dict[str, object] = {
                "answer": raw_answer,
                "provider": "oracle",
                "remoteHost": response.remote_host,
                "durationSeconds": response.duration_seconds,
            }
        else:
            raw_answer = await self._run_aux_codex_turn(
                judge_agent,
                prompt,
                event_log_subdir="judge-codex-events",
                label="judge",
            )
            response_payload = {
                "answer": raw_answer,
                "provider": "codex",
            }
        if self._resources is not None:
            self._write_json(self._resources.run_dir / "last-judge-response.json", response_payload)
        decision = self._parse_judge_decision(raw_answer)
        await self._record_workflow_event(
            "judge_completed",
            f"{judge_agent.provider} returned '{decision.decision}'.",
            payload=decision.model_dump(mode="json"),
        )
        return decision

    async def _check_budgets(
        self,
        loop_index: int,
        *,
        before_judge: bool = False,
    ) -> None:
        if self._run_state is None:
            raise WorkflowSupervisorError("No workflow state is available.")
        elapsed_minutes = (datetime.now(UTC) - self._run_state.started_at).total_seconds() / 60
        if elapsed_minutes >= self._run_state.max_runtime_minutes:
            raise WorkflowSupervisorError(
                f"Workflow runtime budget exceeded ({self._run_state.max_runtime_minutes} minutes)."
            )
        if loop_index > self._run_state.max_loops:
            raise WorkflowSupervisorError(
                f"Workflow loop budget exceeded ({self._run_state.max_loops} loops)."
            )
        if before_judge and self._run_state.judge_calls >= self._run_state.max_judge_calls:
            raise WorkflowSupervisorError(
                f"Workflow judge-call budget exceeded ({self._run_state.max_judge_calls} calls)."
            )

    def _clear_oracle_pause(self, agent_label: Literal["expert", "judge"]) -> None:
        if self._run_state is None:
            return
        checkpoint = self._run_state.oracle_resume_checkpoint
        if checkpoint is not None and checkpoint.agent_label == agent_label:
            self._run_state.oracle_resume_checkpoint = None
        prefix = f"Oracle {agent_label} failed and the run is paused:"
        if self._run_state.last_error and self._run_state.last_error.startswith(prefix):
            self._run_state.last_error = None
        self._run_state.updated_at = datetime.now(UTC)

    async def _pause_for_oracle_failure(
        self,
        *,
        agent_label: Literal["expert", "judge"],
        agent_id: str,
        prompt: str,
        detail: str,
    ) -> None:
        if self._run_state is None:
            raise WorkflowSupervisorError("No workflow run exists.")
        thread_id: str | None = None
        if self._bridge is not None:
            bridge_thread = self._bridge.snapshot().state.thread
            if bridge_thread is not None:
                thread_id = bridge_thread.id
        elif self._archived_snapshot is not None and self._archived_snapshot.state.thread is not None:
            thread_id = self._archived_snapshot.state.thread.id
        if thread_id is None:
            raise WorkflowSupervisorError("Cannot pause for Oracle failure without a Codex thread.")
        self._pause_gate.clear()
        self._run_state.status = "paused"
        self._run_state.phase = "paused"
        self._run_state.oracle_resume_checkpoint = OracleResumeCheckpoint(
            agent_label=agent_label,
            agent_id=agent_id,
            thread_id=thread_id,
            loop_index=max(1, self._run_state.current_loop),
            prompt=prompt,
            detail=detail,
            noted_at=datetime.now(UTC),
        )
        self._run_state.last_error = (
            f"Oracle {agent_label} failed and the run is paused: {detail}"
        )
        self._run_state.updated_at = datetime.now(UTC)
        await self._record_workflow_event(
            "oracle_blocked",
            f"Oracle {agent_label} failed; run paused until operator resume.",
            payload={
                "agent": agent_label,
                "agentId": agent_id,
                "detail": detail,
                "threadId": thread_id,
                "loop": self._run_state.current_loop,
            },
        )
        await self._broadcast_state()
        await self._flush_staged_snapshot_now()
        await self._pause_gate.wait()
        if self._run_state.stop_requested:
            raise WorkflowStoppedError("Workflow stop requested.")

    async def _ensure_checkpoint(self, phase: WorkflowPhase, message: str) -> None:
        if self._run_state is None:
            raise WorkflowSupervisorError("No workflow run exists.")
        if self._run_state.stop_requested:
            raise WorkflowStoppedError("Workflow stop requested.")
        if self._run_state.pause_requested:
            self._pause_gate.clear()
            self._run_state.status = "paused"
            self._run_state.phase = "paused"
            self._run_state.updated_at = datetime.now(UTC)
            await self._record_workflow_event(
                "paused",
                "Workflow run paused between steps.",
            )
            await self._broadcast_state()
            await self._flush_staged_snapshot_now()
            await self._pause_gate.wait()
        if self._run_state.stop_requested:
            raise WorkflowStoppedError("Workflow stop requested.")
        self._run_state.status = "running"
        self._run_state.phase = phase
        self._run_state.updated_at = datetime.now(UTC)
        await self._record_workflow_event("phase_changed", message)

    async def _finish_run(
        self,
        *,
        status: WorkflowRunStatus,
        phase: WorkflowPhase,
        note: str,
    ) -> None:
        if self._run_state is not None:
            self._run_state.status = status
            self._run_state.phase = phase
            self._run_state.oracle_resume_checkpoint = None
            self._run_state.last_error = note if status == "failed" else None
            self._run_state.completed_at = datetime.now(UTC)
            self._run_state.updated_at = datetime.now(UTC)
            await self._record_workflow_event(
                f"run_{status}",
                note,
            )
        await self._stop_bridge()
        await self._broadcast_state()
        await self._flush_staged_snapshot_now()

    async def _record_workflow_event(
        self,
        kind: str,
        message: str,
        *,
        payload: object | None = None,
    ) -> None:
        if self._resources is None:
            return
        record = await self._resources.workflow_event_store.append(
            kind=kind,
            message=message,
            payload=payload,
        )
        self._recent_workflow_events.append(record)
        if self._run_state is not None:
            self._run_state.updated_at = datetime.now(UTC)
        self._stage_run_snapshot()
        await self._broadcast(
            StreamEnvelope(
                type="workflow_event",
                state=self.snapshot().state,
                event=None,
                workflow_event=record,
            )
        )

    async def _broadcast_state(self) -> None:
        self._stage_run_snapshot()
        await self._broadcast(
            StreamEnvelope(
                type="state",
                state=self.snapshot().state,
                event=None,
                workflow_event=None,
            )
        )

    async def _broadcast(self, envelope: StreamEnvelope) -> None:
        stale: list[asyncio.Queue[StreamEnvelope]] = []
        for queue in self._subscribers:
            try:
                queue.put_nowait(envelope)
            except asyncio.QueueFull:
                stale.append(queue)
        for queue in stale:
            self._subscribers.discard(queue)

    async def _build_judge_bundle(
        self,
        codex_output: str,
        *,
        expert_assessment: str | None,
    ) -> str:
        if self._run_state is None:
            raise WorkflowSupervisorError("No workflow run exists.")
        git_status = await self._git_output("status", "--short")
        git_diff_stat = await self._git_output("diff", "--stat")
        git_diff_excerpt = await self._git_output("diff", "--", ".")
        bridge_snapshot = self._bridge.snapshot() if self._bridge is not None else None
        payload = {
            "goal": self._run_state.goal,
            "workflowId": self._run_state.workflow_id,
            "targetDir": self._run_state.target_dir,
            "loop": self._run_state.current_loop,
            "judgeCalls": self._run_state.judge_calls,
            "recentSteeringNotes": self._run_state.recent_steering_notes[-5:],
            "lastPlan": self._run_state.last_plan,
            "lastCodexOutput": self._clip(codex_output, limit=8_000),
            "expertAssessment": self._clip(expert_assessment, limit=8_000),
            "codexLastError": (
                bridge_snapshot.state.turn.error
                if bridge_snapshot is not None and bridge_snapshot.state.turn is not None
                else None
            ),
            "pendingServerRequest": (
                bridge_snapshot.state.pending_server_request.model_dump(mode="json")
                if bridge_snapshot is not None and bridge_snapshot.state.pending_server_request
                else None
            ),
            "gitStatusShort": git_status,
            "gitDiffStat": git_diff_stat,
            "gitDiffExcerpt": self._clip(git_diff_excerpt, limit=8_000),
        }
        return json.dumps(payload, ensure_ascii=True, indent=2)

    async def _run_aux_codex_turn(
        self,
        agent: Any,
        prompt: str,
        *,
        event_log_subdir: str,
        label: str,
    ) -> str:
        if self._run_state is None:
            raise WorkflowSupervisorError("No workflow run exists.")
        if self._resources is None:
            raise WorkflowSupervisorError("No workflow resources are available.")
        bridge = CodexAppServerBridge(
            self._settings,
            workspace_root=Path(self._run_state.target_dir),
            event_log_dir=self._resources.run_dir / event_log_subdir,
            agent_config=CodexAgentConfig(
                role=agent.role,
                startup_prompt=agent.startup_prompt,
                description=agent.description,
                model=agent.model,
                model_provider=agent.model_provider,
                reasoning_effort=agent.reasoning_effort,
                approval_policy=agent.approval_policy or "never",
                sandbox_mode=agent.sandbox_mode or "workspace-write",
                web_access=agent.web_access or "disabled",
                service_tier=agent.service_tier,
            ),
        )
        await bridge.start()
        try:
            snapshot = await bridge.start_turn(prompt)
            turn = snapshot.state.turn
            if turn is None:
                raise WorkflowSupervisorError(f"Codex {label} did not create a turn.")
            completed = await bridge.wait_for_turn_completion(turn.id)
            assistant_text = self._assistant_text_for_turn(completed, turn.id)
            if completed.state.turn and completed.state.turn.error:
                raise WorkflowSupervisorError(completed.state.turn.error)
            if not assistant_text:
                raise WorkflowSupervisorError(
                    f"Codex {label} completed the turn without an assistant message."
                )
            return assistant_text
        finally:
            await bridge.stop()

    async def _git_output(self, *args: str) -> str:
        if self._run_state is None:
            return "no workflow run"
        process = await asyncio.create_subprocess_exec(
            "git",
            "-C",
            self._run_state.target_dir,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(process.communicate(), timeout=15)
        except TimeoutError:
            process.kill()
            await process.wait()
            return "git command timed out"
        stdout_text = stdout_bytes.decode("utf-8", errors="replace").strip()
        stderr_text = stderr_bytes.decode("utf-8", errors="replace").strip()
        if process.returncode != 0:
            return stderr_text or stdout_text or "git command failed"
        return stdout_text or "(empty)"

    def _consume_steering(self, prompt: str) -> str:
        if self._run_state is None or not self._run_state.pending_steering_notes:
            return prompt
        notes = [note.strip() for note in self._run_state.pending_steering_notes if note.strip()]
        self._run_state.pending_steering_notes.clear()
        self._run_state.recent_steering_notes.extend(notes)
        self._run_state.recent_steering_notes = self._run_state.recent_steering_notes[-10:]
        if not notes:
            return prompt
        notes_block = "\n".join(f"- {note}" for note in notes)
        return (
            f"{prompt}\n\nOperator steering to apply on this step:\n"
            f"{notes_block}\n\n"
            "Follow this steering unless it directly conflicts with higher-priority instructions."
        )

    @staticmethod
    def _assistant_text_for_turn(snapshot: DashboardSnapshot, turn_id: str) -> str:
        for item in reversed(snapshot.state.transcript):
            if item.role == "assistant" and item.turn_id == turn_id:
                return item.text.strip()
        return ""

    @staticmethod
    def _git_root_for(path: Path) -> Path | None:
        try:
            completed = subprocess.run(
                ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError:
            return None
        if completed.returncode != 0:
            return None
        root = completed.stdout.strip()
        return Path(root).resolve() if root else None

    @staticmethod
    def _extract_json(text: str) -> str:
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = stripped.strip("`")
            stripped = stripped.removeprefix("json").strip()
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise WorkflowSupervisorError("Judge did not return a JSON object.")
        return stripped[start : end + 1]

    @classmethod
    def _parse_judge_decision(cls, raw_answer: str) -> JudgeDecision:
        json_error: Exception | None = None
        try:
            payload = cls._extract_json(raw_answer)
            try:
                return JudgeDecision.model_validate_json(payload)
            except ValidationError:
                repaired = cls._repair_judge_payload(payload)
                return JudgeDecision.model_validate(repaired)
        except (ValidationError, WorkflowSupervisorError) as exc:
            json_error = exc

        try:
            return cls._parse_judge_text_decision(raw_answer)
        except ValidationError as exc:
            raise WorkflowSupervisorError(
                "Judge returned a malformed decision payload that could not be parsed."
            ) from exc
        except WorkflowSupervisorError as exc:
            raise WorkflowSupervisorError(
                "Judge returned a malformed decision payload that could not be parsed."
            ) from (json_error or exc)

    @classmethod
    def _repair_judge_payload(cls, payload: str) -> dict[str, object]:
        decision_match = re.search(
            r'"decision"\s*:\s*"(?P<decision>continue|complete|fail)"',
            payload,
        )
        if decision_match is None:
            raise WorkflowSupervisorError("Judge decision payload is missing a valid decision.")

        repaired: dict[str, object] = {"decision": decision_match.group("decision")}
        for field_name in (
            "summary",
            "next_prompt",
            "completion_note",
            "failure_reason",
        ):
            field_value = cls._extract_string_field(payload, field_name)
            if field_value is not None:
                repaired[field_name] = field_value
        return repaired

    @classmethod
    def _parse_judge_text_decision(cls, raw_answer: str) -> JudgeDecision:
        text = cls._strip_code_fence(raw_answer)
        sections = cls._extract_judge_text_sections(text)
        if "decision" not in sections:
            raise WorkflowSupervisorError("Judge text response is missing a Decision section.")
        if "summary" not in sections:
            raise WorkflowSupervisorError("Judge text response is missing a Summary section.")

        payload: dict[str, object] = {
            "decision": sections["decision"].strip().lower(),
            "summary": sections["summary"].strip(),
        }
        section_map = {
            "next prompt": "next_prompt",
            "completion note": "completion_note",
            "failure reason": "failure_reason",
        }
        for section_name, field_name in section_map.items():
            value = sections.get(section_name)
            if value:
                payload[field_name] = value.strip()
        return JudgeDecision.model_validate(payload)

    @staticmethod
    def _strip_code_fence(text: str) -> str:
        stripped = text.strip()
        if not stripped.startswith("```"):
            return stripped
        lines = stripped.splitlines()
        if not lines:
            return stripped
        body_lines = lines[1:]
        if body_lines and body_lines[-1].strip() == "```":
            body_lines = body_lines[:-1]
        return "\n".join(body_lines).strip()

    @staticmethod
    def _extract_judge_text_sections(text: str) -> dict[str, str]:
        pattern = re.compile(
            r"(?im)^(Decision|Summary|Next prompt|Completion note|Failure reason)\s*:\s*"
        )
        matches = list(pattern.finditer(text))
        if not matches:
            raise WorkflowSupervisorError("Judge text response does not use the expected labels.")

        sections: dict[str, str] = {}
        for index, match in enumerate(matches):
            section_name = match.group(1).lower()
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            sections[section_name] = text[start:end].strip()
        return sections

    @staticmethod
    def _extract_string_field(payload: str, field_name: str) -> str | None:
        key = f'"{field_name}"'
        key_index = payload.find(key)
        if key_index == -1:
            return None
        colon_index = payload.find(":", key_index + len(key))
        if colon_index == -1:
            return None
        value_index = colon_index + 1
        while value_index < len(payload) and payload[value_index].isspace():
            value_index += 1
        if value_index >= len(payload):
            return None
        if payload.startswith("null", value_index):
            return None
        if payload[value_index] != '"':
            return None

        value_chars: list[str] = []
        index = value_index + 1
        while index < len(payload):
            char = payload[index]
            if char == "\\" and index + 1 < len(payload):
                value_chars.append(char)
                value_chars.append(payload[index + 1])
                index += 2
                continue
            if char == '"':
                lookahead = index + 1
                while lookahead < len(payload) and payload[lookahead].isspace():
                    lookahead += 1
                if lookahead >= len(payload) or payload[lookahead] in {",", "}"}:
                    try:
                        return json.loads('"' + "".join(value_chars) + '"')
                    except json.JSONDecodeError:
                        return "".join(value_chars)
            value_chars.append(char)
            index += 1
        return None

    @staticmethod
    def _render_template(template: str, **values: str) -> str:
        rendered = template
        for key, value in values.items():
            rendered = rendered.replace("{" + key + "}", value)
        return rendered

    @classmethod
    def _render_agent_prompt(
        cls,
        template: str,
        *,
        agent: Any,
        **values: str,
    ) -> str:
        if agent.provider == "oracle":
            prompt_limit = agent.prompt_char_limit or 20_000
            return cls._render_judge_prompt(template, prompt_limit=prompt_limit, **values)
        return cls._render_template(template, **values)

    @classmethod
    def _render_judge_prompt(
        cls,
        template: str,
        *,
        prompt_limit: int,
        **values: str,
    ) -> str:
        current_values = {key: value for key, value in values.items()}
        prompt = cls._render_template(template, **current_values)
        if len(prompt) <= prompt_limit:
            return prompt

        for key in ("judge_bundle", "last_output", "plan", "goal"):
            current = current_values.get(key, "")
            if not current:
                continue
            overflow = len(prompt) - prompt_limit
            if overflow <= 0:
                break
            new_limit = max(256, len(current) - overflow - 256)
            current_values[key] = cls._clip(current, limit=new_limit) or ""
            prompt = cls._render_template(template, **current_values)
            if len(prompt) <= prompt_limit:
                return prompt

        if len(prompt) > prompt_limit:
            return prompt[: prompt_limit - 1] + "…"
        return prompt

    @staticmethod
    def _clip(text: str | None, *, limit: int = 4_000) -> str | None:
        if text is None:
            return None
        stripped = text.strip()
        if len(stripped) <= limit:
            return stripped
        return stripped[: limit - 1] + "…"

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    def _stage_run_snapshot(self) -> None:
        if self._resources is None:
            return
        snapshot = self.snapshot()
        snapshot_path = self._resources.run_dir / self.RUN_SNAPSHOT_FILENAME
        self._archived_snapshot = snapshot.model_copy(deep=True)
        self._staged_snapshot = snapshot
        self._staged_snapshot_path = snapshot_path
        self._snapshot_revision += 1
        self._staged_snapshot_revision = self._snapshot_revision
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            self._write_snapshot_file(snapshot_path, snapshot.model_dump_json(indent=2))
            self._snapshot_flushed_revision = self._staged_snapshot_revision
            return
        if self._snapshot_flush_task is None or self._snapshot_flush_task.done():
            self._snapshot_flush_task = asyncio.create_task(self._flush_staged_snapshot_loop())

    async def _flush_staged_snapshot_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(self.SNAPSHOT_FLUSH_DEBOUNCE_SECONDS)
                await self._flush_staged_snapshot_to_disk()
                if self._snapshot_flushed_revision >= self._snapshot_revision:
                    return
        except asyncio.CancelledError:
            return
        finally:
            current = asyncio.current_task()
            if self._snapshot_flush_task is current:
                self._snapshot_flush_task = None

    async def _flush_staged_snapshot_now(self) -> None:
        await self._cancel_snapshot_flush_task()
        await self._flush_staged_snapshot_to_disk()

    async def _cancel_snapshot_flush_task(self) -> None:
        task = self._snapshot_flush_task
        if task is None:
            return
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        self._snapshot_flush_task = None

    async def _flush_staged_snapshot_to_disk(self) -> None:
        async with self._snapshot_flush_lock:
            snapshot = self._staged_snapshot
            snapshot_path = self._staged_snapshot_path
            revision = self._staged_snapshot_revision
            if snapshot is None or snapshot_path is None:
                return
            payload = snapshot.model_dump_json(indent=2)
            await asyncio.to_thread(self._write_snapshot_file, snapshot_path, payload)
            if revision > self._snapshot_flushed_revision:
                self._snapshot_flushed_revision = revision

    @staticmethod
    def _write_snapshot_file(path: Path, payload: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")


def as_http_error(error: Exception) -> HTTPException:
    if isinstance(error, WorkflowConflictError):
        return HTTPException(status_code=409, detail=str(error))
    if isinstance(error, WorkflowNotFoundError):
        return HTTPException(status_code=404, detail=str(error))
    return HTTPException(status_code=400, detail=str(error))
````

## File: plans/003-workflow-supervisor.md
````markdown
# ExecPlan 003: Declarative Workflow Supervisor

## Summary

Add a thin workflow supervisor on top of the existing Codex bridge and Oracle sidecar so Shmocky
can run a named workflow against a local repo path with minimal human steering. V1 stays narrow:

- one active workflow run at a time
- repo-local TOML config as the source of truth
- one long-lived Codex thread per run
- a linear loop workflow, not a general graph runtime
- Oracle as a structured evaluator that decides `continue`, `complete`, or `fail`

## Scope

In scope:

- typed workflow and agent configuration in repo-local TOML
- a single-run supervisor owning Codex, Oracle, budgets, pause or resume or stop, and steering
- persisted workflow supervisor events under `.shmocky/runs/`
- API endpoints to launch, observe, and control workflow runs
- SPA workflow launcher and control surfaces

Out of scope:

- general DAG execution or agent society orchestration
- repo cloning or git URL intake
- multiple concurrent workflow runs
- browser-based TOML editing

## Architecture

Backend:

- `shmocky.toml` defines `agents` and `workflows`.
- `WorkflowSupervisor` owns the active run, creates a per-run `CodexAppServerBridge`, invokes the
  Oracle sidecar for judge steps, persists workflow events, and exposes combined dashboard state.
- `CodexAppServerBridge` remains the raw app-server transport and transcript projection layer, but
  is now created per target directory rather than once at app startup.
- `OracleAgent` remains a serialized sidecar and is used directly by the supervisor for judge steps.

Frontend:

- the existing transcript and raw protocol panes stay visible
- a new workflow surface launches named workflows, shows loop state and budgets, and offers pause,
  resume, stop, and steer controls

## Milestones

1. Config and runtime
   - add workflow config models and loader
   - add per-run supervisor and persisted workflow events
2. API and state
   - expose workflow catalog and run-control endpoints
   - combine workflow state with existing dashboard state
3. UI
   - add workflow launcher and control surfaces
   - show workflow-level events separately from raw protocol events
4. Validation
   - add focused config and supervisor tests
   - run backend and frontend quality gates

## Validation

- `uv run ruff check .`
- `uv run ty check`
- `uv run --extra dev pytest -q`
- `npm --prefix apps/web run check`
- `npm --prefix apps/web run biome:check`
- focused manual smoke: start a workflow run from the browser and confirm Codex plus Oracle participate

## Open Questions

- whether v2 should allow planner and executor to be separate Codex sessions rather than one shared thread
- whether Oracle should later move to a more typed MCP integration instead of CLI wrapping

## Progress Notes

- 2026-03-31: Locked v1 product shape to repo-local TOML, linear loop workflows, local target directories, and one active run at a time.
- 2026-03-31: Added backend workflow models, config loader, workflow supervisor skeleton, per-run Codex session startup, and combined workflow plus transcript dashboard state.
- 2026-03-31: Added `shmocky.toml`, workflow APIs, SPA run launcher and controls, workflow event projection, and focused config plus supervisor tests.
- 2026-03-31: Focused end-to-end smoke passed with a temporary one-loop workflow against a throwaway git repo, confirming Codex planning and execution plus Oracle structured completion judging.
- 2026-03-31: Smoke testing surfaced a real template-rendering bug with literal JSON braces in judge prompts; prompt rendering now replaces only known placeholders and leaves other braces intact.
- 2026-03-31: Added target-directory isolation guards so runs reject directories inside the Shmocky repo or nested inside another git repository unless explicitly overridden.
- 2026-03-31: Moved Oracle prompt-size policy to Oracle agent config with `prompt_char_limit` in `shmocky.toml`, while keeping the global env setting as a fallback for ad hoc Oracle queries.
- 2026-03-31: Rebalanced the operator UI so workflow activity remains in the primary right-rail view, with the protocol stream moved behind a dedicated debug tab instead of always consuming vertical space.
- 2026-03-31: Added durable per-run dashboard snapshots plus history APIs and a browser run selector, so completed runs can be reopened with transcript, workflow activity, and recent protocol context intact.
- 2026-03-31: Relaxed the Oracle judge contract from strict JSON to a labeled plain-text decision format, while keeping JSON parsing as a backward-compatible fallback.
- 2026-03-31: Split advisory and control roles so Oracle can act as a free-text expert while a Codex judge owns workflow decisions, making cross-agent handoff observable without relying on Oracle for structured control output.
- 2026-04-01: Added per-Oracle-agent `chatgpt_url` support so advisory runs can be directed into dedicated ChatGPT project folders instead of cluttering the main browser history.
- 2026-04-01: Oracle-side failures now pause workflow runs in a resumable state instead of failing outright, and the default Oracle wait budget was raised to one hour for slower browser-model calls.
- 2026-04-01: Added live browser handling for pending app-server requests, including approval and request-user-input responses, and fixed pending-request clearing to follow the protocol's `requestId` field.
- 2026-04-01: Added durable resume semantics for Oracle-blocked pauses by persisting a restart-safe checkpoint, restoring the paused run at startup, and resuming the saved Codex thread before retrying the blocked Oracle step.
- 2026-04-01: Restricted Oracle file attachments to the configured workspace root, rejecting absolute paths and `..`-based escapes so ad hoc Oracle queries cannot attach arbitrary server files.
- 2026-04-01: Hardened startup rollback so a failed Codex initialize cannot leave the bridge process or supervisor run state wedged in `starting`; failed starts now clean up the child app-server and clear provisional run state so later runs can proceed.
- 2026-04-01: Propagated app-server death to bridge callers so pending RPC requests fail immediately and turn waiters stop hanging if Codex exits mid-request or mid-turn.
- 2026-04-01: Debounced dashboard snapshot persistence so streaming bridge events stage in-memory snapshots and flush to disk in batched background writes, while pause/finish/shutdown boundaries still force an immediate durable snapshot.
- 2026-04-01: Oracle sidecar temp output files are now cleaned up from the outer query path so timeouts and subprocess-start failures do not leak orphaned files under `.shmocky/oracle/`.
````
