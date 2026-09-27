# Generated contracts

These files are derived from runtime sources by `scripts/generate_docs_contracts.py`.

Do not edit them manually. Update the runtime source or generator, then run:

```bash
python scripts/generate_docs_contracts.py
python scripts/generate_docs_contracts.py --check
```

Generated artifacts:

- `STATE_DB.md` — state schema DDL, indexes and ER relationships.
- `CONTENT_DB.md` — content schema DDL, indexes and ER relationships.
- `WEBSOCKET_CONTRACTS.md` — human-readable WebSocket command contract table.
- `websocket-contracts.json` — machine-readable WebSocket command metadata.
