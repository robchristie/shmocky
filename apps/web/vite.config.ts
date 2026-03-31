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
