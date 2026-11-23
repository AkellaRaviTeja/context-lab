"""Chapter 21's Mem0 arm, in a process of its own, with every outside connection refused.

    uv run python lessons/21-frameworks-review/mem0_arm.py --telemetry off   # the four tasks
    uv run python lessons/21-frameworks-review/mem0_arm.py --telemetry on    # start-up only

run.py starts it twice. Mem0 reads MEM0_TELEMETRY when it is imported, so the setting must be
in the environment before the import, which is why the arm has its own process. Both runs are
inside `lantern.network.watch()`: a library that tries to reach the outside is counted and
refused, whatever its settings say. The last line printed is the arm's result as JSON.

Needs the optional extra (`uv sync --extra memory`) and Ollama with qwen3:8b and
nomic-embed-text. With telemetry on, only start-up and one stored line without the model are
run: enough to see what it tries to send.
"""

import argparse
import json
import os
import shutil
import sys
import time
import traceback

from lantern import frameworks, memory, network
from lantern.config import ROOT, load_config, model_name

parser = argparse.ArgumentParser()
parser.add_argument("--telemetry", choices=("on", "off"), default="off")
args = parser.parse_args()

folder = ROOT / ".scratch" / "21" / f"mem0-telemetry-{args.telemetry}"
shutil.rmtree(folder, ignore_errors=True)
folder.mkdir(parents=True)
os.environ["MEM0_DIR"] = str(folder)  # its own settings file, not ~/.mem0
if args.telemetry == "off":
    os.environ["MEM0_TELEMETRY"] = "False"
else:
    os.environ.pop("MEM0_TELEMETRY", None)

out: dict = {"telemetry": args.telemetry, "ran": False}
with network.watch(refuse_outside=True) as net:
    start = time.perf_counter()
    try:
        from mem0 import Memory

        cfg = load_config()
        m = Memory.from_config(frameworks.mem0_config(
            folder, host=cfg["ollama"]["host"], model=model_name(None)))
        out["seconds_start"] = round(time.perf_counter() - start, 1)
        if args.telemetry == "off":
            m10 = memory.from_case().get("M-10")
            out.update(frameworks.mem0_tasks(m, sourced=m10.text, sourced_source=m10.source,
                                                 sourced_author=m10.author))
        else:
            m.add([{"role": "user", "content": frameworks.EIGHTH}], user_id="eow-fin-07",
                  run_id=frameworks.INQUIRY, infer=False)
            m.get_all(filters={"run_id": frameworks.INQUIRY})
            time.sleep(8)  # telemetry is sent from a background thread
        out["ran"] = True
    except Exception as e:  # the arm reports what failed; the chapter records it as not run
        out["error"] = f"{type(e).__name__}: {e}"
        out["trace"] = traceback.format_exc()[-1500:]
    out["seconds"] = {**out.get("seconds", {}), "total": round(time.perf_counter() - start, 1)}
    out["network"] = net.summary()
    print(json.dumps(out, default=str), flush=True)
    sys.stderr.flush()
    # Leave from inside the watch: a library's exit handlers (a last telemetry flush) would
    # otherwise run after the watch has been taken down.
    os._exit(0)
