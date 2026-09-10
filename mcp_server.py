import sys
import json
from client import ARIESRecoveryEngine

def main():
    engine = ARIESRecoveryEngine()
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        req = json.loads(line)
        method = req.get("method")
        params = req.get("params", {})
        if method == "log_update":
            lsn = engine.log_update(params.get("tx_id"), params.get("page_id"), params.get("key"), params.get("old_val"), params.get("new_val"))
            res = {"lsn": lsn}
        elif method == "log_commit":
            lsn = engine.log_commit(params.get("tx_id"))
            res = {"lsn": lsn}
        elif method == "recover":
            res = engine.recover(params.get("disk_state", {}))
        else:
            res = {"error": "unknown method"}
        sys.stdout.write(json.dumps({"id": req.get("id"), "result": res}) + "\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
