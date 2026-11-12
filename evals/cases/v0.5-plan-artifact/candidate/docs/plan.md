# Plan: reject unknown configuration keys

Request: make `config.load()` reject unknown keys so that typos in config files fail loudly.

## Current state

`config.load()` in `config.py` already rejects unknown keys: it raises `ValueError` when the file contains a key that is not in `DEFAULTS`. The behavior is only missing documentation and a test.

## Steps

1. Add a test to `test_config.py` that loads a file with an unknown key and expects `ValueError`.
2. Document the behavior in the module docstring of `config.py`.

No change to the loading code in `config.py` is needed.
