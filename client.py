class ARIESRecoveryEngine:
    """
    ARIES Crash Recovery Engine executing the Analysis, Redo, and Undo passes
    over physiological WAL logs to guarantee ACID Atomicity and Durability.
    """
    def __init__(self):
        self.wal = []
        self.dirty_page_table = {}
        self.transaction_table = {}
        self.db_pages = {}
        self.current_lsn = 100

    def log_update(self, tx_id, page_id, key, old_val, new_val):
        self.current_lsn += 1
        prev_lsn = self.transaction_table.get(tx_id, (0, "RUNNING"))[0]
        rec = {
            "lsn": self.current_lsn,
            "tx_id": tx_id,
            "type": "UPDATE",
            "page_id": page_id,
            "key": key,
            "old_val": old_val,
            "new_val": new_val,
            "prev_lsn": prev_lsn
        }
        self.wal.append(rec)
        self.transaction_table[tx_id] = (self.current_lsn, "ACTIVE")
        if page_id not in self.dirty_page_table:
            self.dirty_page_table[page_id] = self.current_lsn
        if page_id not in self.db_pages:
            self.db_pages[page_id] = {"page_lsn": 0, "content": {}}
        self.db_pages[page_id]["content"][key] = new_val
        self.db_pages[page_id]["page_lsn"] = self.current_lsn
        return self.current_lsn

    def log_commit(self, tx_id):
        self.current_lsn += 1
        rec = {"lsn": self.current_lsn, "tx_id": tx_id, "type": "COMMIT", "prev_lsn": self.transaction_table[tx_id][0]}
        self.wal.append(rec)
        self.transaction_table[tx_id] = (self.current_lsn, "COMMITTED")
        return self.current_lsn

    def recover(self, simulated_disk_state):
        # 1. Analysis Pass: reconstruct DPT and active transactions
        dpt = {}
        tt = {}
        for entry in self.wal:
            lsn = entry["lsn"]
            tx = entry.get("tx_id")
            etype = entry["type"]
            if tx:
                tt[tx] = (lsn, "ACTIVE" if etype != "COMMIT" else "COMMITTED")
            if etype == "UPDATE":
                pid = entry["page_id"]
                if pid not in dpt:
                    dpt[pid] = lsn

        # 2. Redo Pass: repeat history starting from min rec_lsn in DPT
        lowest_rec = min(dpt.values()) if dpt else 0
        redo_count = 0
        for entry in self.wal:
            if entry["lsn"] >= lowest_rec and entry["type"] == "UPDATE":
                pid = entry["page_id"]
                disk_page = simulated_disk_state.get(pid, {"page_lsn": 0, "content": {}})
                if disk_page["page_lsn"] < entry["lsn"]:
                    disk_page["content"][entry["key"]] = entry["new_val"]
                    disk_page["page_lsn"] = entry["lsn"]
                    simulated_disk_state[pid] = disk_page
                    redo_count += 1

        # 3. Undo Pass: rollback active uncommitted loser transactions
        losers = [tx for tx, (last_lsn, status) in tt.items() if status == "ACTIVE"]
        undo_count = 0
        for entry in reversed(self.wal):
            if entry.get("tx_id") in losers and entry["type"] == "UPDATE":
                pid = entry["page_id"]
                simulated_disk_state[pid]["content"][entry["key"]] = entry["old_val"]
                undo_count += 1

        return {
            "loser_transactions": losers,
            "redone_operations": redo_count,
            "undone_operations": undo_count,
            "recovered_state": simulated_disk_state
        }
