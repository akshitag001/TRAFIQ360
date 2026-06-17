import sys
import time
import threading
import traceback

def dump_stack():
    time.sleep(2)
    print("\n--- Main thread stack trace ---", flush=True)
    for thread_id, stack in sys._current_frames().items():
        if thread_id == threading.main_thread().ident:
            print("".join(traceback.format_stack(stack)), flush=True)
    print("--- End stack trace ---\n", flush=True)

t = threading.Thread(target=dump_stack, daemon=True)
t.start()

print("Importing pulp...", flush=True)
import pulp
print("pulp imported successfully!", flush=True)
