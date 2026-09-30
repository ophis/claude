# linear skill — setup

One-time, per machine:

1. In Linear: Settings → Account → Security & access → Personal API keys → create a key. The key acts as the user who created it.
2. Store it in the Keychain (paste the key at the prompt):
   ```bash
   security add-generic-password -s linear-api-key -a "$USER" -w
   ```
3. Check: `python3 scripts/linear.py '{ viewer { name } }'`.

Alternatively, set `LINEAR_API_KEY` in the environment; it takes precedence over the default Keychain item.

## Several keys

Store each key under its own service and pick one per call; `LINEAR_KEYCHAIN_SERVICE` overrides `LINEAR_API_KEY` and never falls back to `linear-api-key`:

```bash
security add-generic-password -s linear-api-key-agent -a agent -w
LINEAR_KEYCHAIN_SERVICE=linear-api-key-agent python3 scripts/linear.py '{ viewer { name } }'
```

Without `-a`, a lookup returns any one item of the service, so keep one item per service or set `LINEAR_KEYCHAIN_ACCOUNT`.
