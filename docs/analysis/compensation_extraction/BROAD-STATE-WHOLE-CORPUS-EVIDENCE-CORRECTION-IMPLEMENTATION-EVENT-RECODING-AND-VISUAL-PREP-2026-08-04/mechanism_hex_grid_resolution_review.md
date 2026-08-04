# Hex-grid resolution review

I evaluated 40 km, 50 km, and 75 km national hex radii as specifications. A fixed 50 km radius is the primary recommendation: 40 km is likely too sparse for the bounded event corpus, while 75 km risks merging distinct metropolitan concentrations. The grid must be generated once in EPSG:5070 and reused for every mechanism and side.

The repository does not contain validated municipality latitude/longitude fields. I therefore did not generate provisional cells from municipality names or substitute state centroids. The event layer is ready for an authoritative coordinate join; the row-level hex layer remains empty until that join occurs.
