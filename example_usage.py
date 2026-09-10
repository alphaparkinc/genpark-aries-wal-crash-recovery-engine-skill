from client import ARIESRecoveryEngine

def main():
    print("=== Testing ARIES WAL Crash Recovery Engine ===")
    aries = ARIESRecoveryEngine()
    aries.log_update("T1", 1, "balance", 100, 150)
    aries.log_update("T2", 2, "balance", 500, 400)
    aries.log_commit("T1")

    simulated_disk = {
        1: {"page_lsn": 0, "content": {"balance": 100}},
        2: {"page_lsn": 0, "content": {"balance": 500}}
    }
    res = aries.recover(simulated_disk)
    print("Recovery Results:")
    print("  Losers:", res["loser_transactions"])
    print("  Redone:", res["redone_operations"])
    print("  Undone:", res["undone_operations"])

    assert "T2" in res["loser_transactions"]
    assert res["recovered_state"][1]["content"]["balance"] == 150
    assert res["recovered_state"][2]["content"]["balance"] == 500
    print("=== All tests passed successfully! ===")

if __name__ == "__main__":
    main()
