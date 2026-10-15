import { appendFileSync, mkdirSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import { execSync } from "child_process";

const __dirname = dirname(fileURLToPath(import.meta.url));
// This file lives at portal/scripts/lib/importActions.ts, so three levels up is
// the repo root (not two — that lands in portal/scripts/).
const root = resolve(__dirname, "../../../");
const portalRoot = resolve(__dirname, "../..");

// Append-only JSONL log of every build/import action. One line per event.
//
// Why this exists: a long-running buildData run stamps a deterministic uuid
// onto every species node and writes those uuids back into the source family
// files. If that run is killed partway through (a session closes, a machine
// reboots, OOM), nothing on disk says "this build started at T, stamped these
// families, and died here" — the tree is simply left half-stamped with no
// record of what produced it. That is exactly how the 2026-10-13 uuid
// backfill ended up uncommitted and untraceable.
//
// So every action logs start, and logs finish/error/interrupted. The
// uuid-stamp events record per-family what was written, which is the detail
// that lets you reconstruct "what produced the missing uuids" after the fact.
// The file is JSONL by design: appends are atomic single-line writes, so a
// crash can never corrupt earlier entries, and tailing it is trivial.
export const ACTIONS_PATH = resolve(portalRoot, "data/import-actions.jsonl");

export type ActionEvent =
  | "start"
  | "finish"
  | "error"
  | "interrupted"
  | "uuid-stamp"
  | "uuid-skip";

export interface ActionEntry {
  ts: string;
  event: ActionEvent;
  pid: number;
  host: string;
  kingdom: string;
  command: string;
  gitSha?: string;
  [key: string]: unknown;
}

let _gitSha: string | undefined;
function gitSha(): string | undefined {
  if (_gitSha !== undefined) return _gitSha;
  try {
    _gitSha = execSync("git rev-parse --short HEAD", {
      cwd: root, timeout: 3000, stdio: "ignore",
    }).toString().trim();
  } catch {
    _gitSha = "";
  }
  return _gitSha || undefined;
}

export function logAction(
  event: ActionEvent,
  kingdom: string,
  detail: Record<string, unknown> = {},
): void {
  try {
    if (!existsSync(dirname(ACTIONS_PATH))) mkdirSync(dirname(ACTIONS_PATH), { recursive: true });
    const entry: ActionEntry = {
      ts: new Date().toISOString(),
      event, pid: process.pid, host: process.env.HOSTNAME || "localhost",
      kingdom, command: (process.argv.slice(2).join(" ") || "(none)"),
      gitSha: gitSha(), ...detail,
    };
    appendFileSync(ACTIONS_PATH, JSON.stringify(entry) + "\n");
  } catch {
    // Logging must never break the build. Silently drop.
  }
}

// Install signal handlers that write an `interrupted` event before exit.
// Returns the kingdom used so callers can keep it in scope.
export function installInterruptHandlers(kingdom: string): void {
  const handler = (sig: NodeJS.Signals) => {
    logAction("interrupted", kingdom, { signal: sig, note: "build killed before finish event" });
    process.exit(130);
  };
  process.once("SIGINT", handler);
  process.once("SIGTERM", handler);
}