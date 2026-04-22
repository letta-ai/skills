#!/usr/bin/env npx tsx
/**
 * Datadog CLI - Direct API access to Datadog observability data
 *
 * Requires:
 *   DD_API_KEY         - Datadog API key (32-char hex from Organization Settings -> API Keys)
 *   DD_APP_KEY         - Datadog Application key (from Organization Settings -> Application Keys)
 *
 * Optional:
 *   DD_SITE            - Datadog site (default: datadoghq.com)
 */

const DD_API_KEY = process.env.DD_API_KEY;
const DD_APP_KEY = process.env.DD_APP_KEY || process.env.DD_APPLICATION_KEY;
const DD_SITE = process.env.DD_SITE || "datadoghq.com";

function getApiBase(): string {
  if (DD_SITE === "datadoghq.com") return "https://api.datadoghq.com";
  if (DD_SITE === "datadoghq.eu") return "https://api.datadoghq.eu";
  return `https://api.${DD_SITE}`;
}

async function ddRequest(method: string, path: string, body?: object): Promise<unknown> {
  if (!DD_API_KEY || !DD_APP_KEY) {
    throw new Error(
      "Missing Datadog credentials.\n" +
      "Set DD_API_KEY and DD_APP_KEY environment variables.\n\n" +
      "Get them from Datadog:\n" +
      "  API Key: Organization Settings -> API Keys\n" +
      "  App Key: Organization Settings -> Application Keys"
    );
  }

  const url = `${getApiBase()}${path}`;
  const headers: Record<string, string> = {
    "DD-API-KEY": DD_API_KEY,
    "DD-APPLICATION-KEY": DD_APP_KEY,
    "Content-Type": "application/json",
  };

  const response = await fetch(url, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const text = await response.text();
    let errorMsg = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const json = JSON.parse(text);
      if (json.errors) errorMsg += `\n${JSON.stringify(json.errors)}`;
    } catch {
      if (text) errorMsg += `\n${text}`;
    }
    throw new Error(errorMsg);
  }

  return response.json();
}

function parseTime(timeStr: string): number {
  const now = Date.now();
  if (timeStr.startsWith("-")) {
    const match = timeStr.match(/^-(\d+)([smhd])$/);
    if (match) {
      const [, num, unit] = match;
      const mult: Record<string, number> = { s: 1000, m: 60000, h: 3600000, d: 86400000 };
      return now - parseInt(num ?? "0") * (mult[unit ?? "s"] ?? 1000);
    }
  }
  const parsed = Date.parse(timeStr);
  return isNaN(parsed) ? now - 3600000 : parsed;
}

async function validate(): Promise<void> {
  const result = (await ddRequest("GET", "/api/v1/validate")) as { valid: boolean };
  console.log(result.valid ? `Credentials valid! Site: ${DD_SITE}` : "Credentials invalid");
  if (!result.valid) process.exit(1);
}

async function searchLogs(query: string, from: string, limit: number): Promise<void> {
  const result = await ddRequest("POST", "/api/v2/logs/events/search", {
    filter: {
      query,
      from: new Date(parseTime(from)).toISOString(),
      to: new Date().toISOString(),
    },
    sort: "-timestamp",
    page: { limit },
  });
  console.log(JSON.stringify(result, null, 2));
}

async function queryMetrics(query: string, from: string, to: string): Promise<void> {
  const params = new URLSearchParams({
    query,
    from: Math.floor(parseTime(from) / 1000).toString(),
    to: Math.floor(parseTime(to) / 1000).toString(),
  });
  const result = await ddRequest("GET", `/api/v1/query?${params}`);
  console.log(JSON.stringify(result, null, 2));
}

async function listMonitors(query?: string): Promise<void> {
  const params = query ? `?query=${encodeURIComponent(query)}` : "";
  const result = await ddRequest("GET", `/api/v1/monitor${params}`);
  console.log(JSON.stringify(result, null, 2));
}

async function getMonitor(id: string): Promise<void> {
  const result = await ddRequest("GET", `/api/v1/monitor/${id}`);
  console.log(JSON.stringify(result, null, 2));
}

async function listIncidents(): Promise<void> {
  const result = await ddRequest("GET", "/api/v2/incidents");
  console.log(JSON.stringify(result, null, 2));
}

async function listHosts(filter?: string): Promise<void> {
  const params = filter ? `?filter=${encodeURIComponent(filter)}` : "";
  const result = await ddRequest("GET", `/api/v1/hosts${params}`);
  console.log(JSON.stringify(result, null, 2));
}

async function listDashboards(): Promise<void> {
  const result = await ddRequest("GET", "/api/v1/dashboard");
  console.log(JSON.stringify(result, null, 2));
}

async function searchSpans(query: string, from: string, limit: number): Promise<void> {
  const result = await ddRequest("POST", "/api/v2/spans/events/search", {
    filter: {
      query,
      from: new Date(parseTime(from)).toISOString(),
      to: new Date().toISOString(),
    },
    page: { limit },
  });
  console.log(JSON.stringify(result, null, 2));
}

async function listServices(): Promise<void> {
  const result = await ddRequest("GET", "/api/v1/service_dependencies");
  console.log(JSON.stringify(result, null, 2));
}

function printUsage(): void {
  console.log(`Datadog CLI - Direct API access

Usage: npx tsx datadog.ts <command> [args]

Commands:
  validate                          Test credentials
  search-logs <query> [--from -1h] [--limit 50]
  query-metrics <query> [--from -1h] [--to now]
  list-monitors [--query <filter>]
  get-monitor <id>
  list-incidents
  list-hosts [--filter <filter>]
  list-dashboards
  search-spans <query> [--from -1h] [--limit 50]
  list-services

Environment:
  DD_API_KEY    Datadog API key (required)
  DD_APP_KEY    Datadog Application key (required)
  DD_SITE       Datadog site (default: datadoghq.com)

Examples:
  npx tsx datadog.ts validate
  npx tsx datadog.ts search-logs "status:error" --from -1h
  npx tsx datadog.ts query-metrics "avg:system.cpu.user{*}" --from -4h
  npx tsx datadog.ts list-monitors --query "status:alert"
`);
}

function parseArgs(args: string[]): { cmd: string; pos: string[]; flags: Record<string, string> } {
  const flags: Record<string, string> = {};
  const pos: string[] = [];
  let cmd = "";
  for (let i = 0; i < args.length; i++) {
    const arg = args[i] ?? "";
    if (arg.startsWith("--")) {
      flags[arg.slice(2)] = args[++i] || "";
    } else if (!cmd) {
      cmd = arg;
    } else {
      pos.push(arg);
    }
  }
  return { cmd, pos, flags };
}

async function main(): Promise<void> {
  const { cmd, pos, flags } = parseArgs(process.argv.slice(2));

  if (!cmd || cmd === "--help" || cmd === "-h") {
    printUsage();
    return;
  }

  try {
    switch (cmd) {
      case "validate": await validate(); break;
      case "search-logs": await searchLogs(pos[0] || "*", flags.from || "-1h", parseInt(flags.limit || "50")); break;
      case "query-metrics": {
        if (!pos[0]) throw new Error("Metric query required");
        await queryMetrics(pos[0], flags.from || "-1h", flags.to || "-0s");
        break;
      }
      case "list-monitors": await listMonitors(flags.query); break;
      case "get-monitor": {
        if (!pos[0]) throw new Error("Monitor ID required");
        await getMonitor(pos[0]);
        break;
      }
      case "list-incidents": await listIncidents(); break;
      case "list-hosts": await listHosts(flags.filter); break;
      case "list-dashboards": await listDashboards(); break;
      case "search-spans": await searchSpans(pos[0] || "*", flags.from || "-1h", parseInt(flags.limit || "50")); break;
      case "list-services": await listServices(); break;
      default: console.error(`Unknown: ${cmd}`); printUsage(); process.exit(1);
    }
  } catch (e) {
    console.error("Error:", e instanceof Error ? e.message : e);
    process.exit(1);
  }
}

main();
