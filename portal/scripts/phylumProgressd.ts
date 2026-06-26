import { argv } from "process";

const progressdUrl = process.env.PROGRESSD_URL || "http://localhost:9876";

function printUsage() {
  console.log("Usage: npx tsx scripts/phylumProgressd.ts --id <id> --label <label> --pct <pct> --msg <message> [--done]");
  console.log();
  console.log("Options:");
  console.log("  --id <session_id>     e.g., gap_tentaculata");
  console.log("  --label <label>       e.g., 'Tentaculata Gap Enrichment'");
  console.log("  --pct <percentage>    e.g., 42.5");
  console.log("  --msg <message>       e.g., 'Fetching species...'");
  console.log("  --done                Mark session as completed");
}

async function run() {
  const args = argv.slice(2);
  let id = "";
  let label = "";
  let pct = 0;
  let msg = "";
  let done = false;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--id" && args[i + 1]) {
      id = args[i + 1];
      i++;
    } else if (args[i] === "--label" && args[i + 1]) {
      label = args[i + 1];
      i++;
    } else if (args[i] === "--pct" && args[i + 1]) {
      pct = parseFloat(args[i + 1]);
      i++;
    } else if (args[i] === "--msg" && args[i + 1]) {
      msg = args[i + 1];
      i++;
    } else if (args[i] === "--done") {
      done = true;
    }
  }

  if (!id || !label || !msg) {
    printUsage();
    process.exit(1);
  }

  const payload = {
    message: msg,
    pct,
    done,
    label
  };

  try {
    const res = await fetch(`${progressdUrl}/api/sessions/${id}/progress`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      console.log(`Successfully updated progressd session '${id}' (${pct}% - ${msg})`);
    } else {
      console.error(`Failed to update progressd: ${res.status} ${res.statusText}`);
      process.exit(1);
    }
  } catch (e: any) {
    console.error(`Failed to connect to progressd at ${progressdUrl}: ${e.message}`);
    process.exit(1);
  }
}

run();
