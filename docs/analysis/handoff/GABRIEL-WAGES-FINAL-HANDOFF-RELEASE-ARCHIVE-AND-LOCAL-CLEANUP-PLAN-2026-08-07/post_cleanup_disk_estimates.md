# Post-cleanup disk estimates

| Scenario | Expected local footprint | Expected saving versus current historical project |
|---|---:|---:|
| No cleanup | 120.85 GiB | 0 B |
| Conservative strip | 34.08 GiB | 86.76 GiB |
| Full historical-project retirement | 31.44 MiB | 120.81 GiB |
| Full retirement + extracted source library | 53.46 GiB | 67.39 GiB |
| Full retirement + compressed parts + extracted library | 98.19 GiB | 22.66 GiB |

The extracted-library scenario uses 56,164,354,195 original-source bytes plus 1,201,303,562 extracted-text bytes. The final deletion task must remeasure immediately before and after each approved wave.
