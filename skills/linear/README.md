# linear skill — setup

One-time, per machine:

1. In Linear: Settings → Account → Security & access → Personal API keys → create a key. The key acts as the user who created it.
2. Store it in the Keychain (paste the key at the prompt):
   ```bash
   security add-generic-password -s linear-api-key -a "$USER" -w
   ```
3. Check: `python3 scripts/linear.py '{ viewer { name } }'`.

Alternatively, set `LINEAR_API_KEY` in the environment; it takes precedence over the Keychain.

## Several keys

The lookup matches on service `linear-api-key` only, so with several items (e.g. your own key and an agent's) the Keychain returns any one of them. Store each under its own account name and pick one per call:

```bash
security add-generic-password -s linear-api-key -a agent -w
LINEAR_KEYCHAIN_ACCOUNT=agent python3 scripts/linear.py '{ viewer { name } }'
```
