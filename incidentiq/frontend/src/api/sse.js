// Simulated SSE-style progress stream for the upload -> parse -> report flow.
//
// The real backend does upload+parse inside one POST and the report is built
// from a second GET, so there's no server push to listen to yet. This fakes
// the fine-grained "stage" events a real SSE endpoint would emit — each
// stage is held open for at least MIN_STAGE_MS so the UI never blinks
// through a step invisibly — while the actual network calls happen at the
// right point in the sequence. Swapping in a real EventSource later only
// means changing runStagedFlow's internals, not any caller.

const MIN_STAGE_MS = 350;

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Run a sequence of stages, calling onStage(index) as each one starts and
 * awaiting its (optional) work before moving on.
 *
 * @param {Array<{label: string, run?: (prev: any) => Promise<any>}>} stages
 * @param {(index: number) => void} onStage
 * @returns {Promise<any>} the return value of the last stage with a `run`
 */
export async function runStagedFlow(stages, onStage) {
  let result;

  for (let i = 0; i < stages.length; i += 1) {
    onStage(i);
    const { run } = stages[i];
    const startedAt = performance.now();

    if (run) {
      result = await run(result);
    }

    const elapsed = performance.now() - startedAt;
    if (elapsed < MIN_STAGE_MS) {
      await wait(MIN_STAGE_MS - elapsed);
    }
  }

  return result;
}
