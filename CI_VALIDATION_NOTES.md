[1mdiff --git a/docs/CI_VALIDATION_NOTES.md b/docs/CI_VALIDATION_NOTES.md[m
[1mnew file mode 100644[m
[1mindex 0000000..d3db163[m
[1m--- /dev/null[m
[1m+++ b/docs/CI_VALIDATION_NOTES.md[m
[36m@@ -0,0 +1,20 @@[m
[32m+[m[32m﻿# Pull Request CI Verification[m
[32m+[m
[32m+[m[32m## Purpose[m
[32m+[m[32mDemonstrate automated validation of a proposed network change.[m
[32m+[m
[32m+[m[32m## Required checks[m
[32m+[m[32m- YAML linting and data validation[m
[32m+[m[32m- Jinja2 configuration rendering[m
[32m+[m[32m- Python unit tests[m
[32m+[m[32m- Batfish reachability and security analysis[m
[32m+[m
[32m+[m[32m## Security expectations[m
[32m+[m[32m- HQ Staff HTTPS to the HQ server should be reachable.[m
[32m+[m[32m- HQ Guest HTTPS to the HQ server should be blocked.[m
[32m+[m[32m- An intentionally unsafe guest-access change should fail validation.[m
[32m+[m
[32m+[m[32m## Limitation[m
[32m+[m[32mThese tests use generated reference configurations.[m
[32m+[m[32mThey do not prove that the Packet Tracer devices have been[m
[32m+[m[32mautomatically deployed to or rolled back.[m
