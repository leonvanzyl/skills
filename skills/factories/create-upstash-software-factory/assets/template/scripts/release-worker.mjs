// Frees a worker that is stuck as busy. That happens when a factory run is
// cancelled or crashes before it can release its Box. Check the Actions tab
// first: if a run is still using the worker, leave it alone.
//
// Run with: node --env-file=.env scripts/release-worker.mjs <worker id>
import { Box } from "@upstash/box"
import { loadConfig } from "../src/config.mjs"
import { getWorkerStates } from "../src/workers.mjs"
import { sh, q } from "../src/box.mjs"
import { secretPaths } from "../src/agents.mjs"

const config = loadConfig()
const workerId = process.argv[2]
const states = await getWorkerStates(config)
if (!states.some((w) => w.id === workerId)) throw new Error(`Unknown worker id: ${workerId}. Known workers: ${states.map((w) => w.id).join(", ")}`)
const worker = states.find((w) => w.id === workerId)
if (!worker?.boxId) throw new Error("Usage: release-worker.mjs <worker id> (the worker must have a Box)")

const box = await Box.get(worker.boxId)

// Clean up first and free the worker last, so no new run can claim the Box
// while its sign-in folder is being deleted. A cancelled run never reached its
// own cleanup.
if (worker.boxStatus === "paused") await box.resume()
await sh(box, `rm -rf ${secretPaths(config).map(q).join(" ")} ~/.git-credentials`, { allowFailure: true })
console.log("Removed any sign-in files left by the interrupted run.")
await box.pause().catch(() => {})

for (const label of await box.labels.list()) {
  if (label === config.factory.busyLabel || label.startsWith("run-")) {
    await box.labels.remove(label)
    console.log(`Removed label ${label}`)
  }
}
console.log(`Worker ${worker.id} is free and its Box is paused.`)
