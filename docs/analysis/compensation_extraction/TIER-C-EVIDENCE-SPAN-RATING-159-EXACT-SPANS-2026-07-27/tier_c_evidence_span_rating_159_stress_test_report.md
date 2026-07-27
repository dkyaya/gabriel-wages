# Stress-test report

- Manifest/hash/ID/count/status drift fails closed before calls.
- Inputs omit source identity and contain only exact span plus bounded context.
- Wrong IDs, mechanisms, controls, quote substrings, boundary booleans, or forbidden final-claim language fail strict validation.
- Invalid responses receive one bounded retry and then quarantine.
- Partial packages cannot pass completion validation.
