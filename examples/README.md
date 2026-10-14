# Example generated configurations

The `reference-output/` directory contains examples generated from the current YAML/Jinja2 source using `--mode ci`. They contain **synthetic CI-only IPsec pre-shared keys**, omit/reduce parts of the actual P1 running configuration, and are for reading/review only. Never paste or deploy them into Packet Tracer or an IOS device. The authoritative source is `data/` plus `templates/`; regenerate with `python scripts/render_configs.py --mode ci --output build/rendered`.
