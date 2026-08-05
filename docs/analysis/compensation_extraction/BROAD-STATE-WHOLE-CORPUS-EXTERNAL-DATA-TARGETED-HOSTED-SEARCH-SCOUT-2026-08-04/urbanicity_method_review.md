# Urbanicity method review

The derived layer uses the U.S. Census Bureau's 2020 Urban Area-to-Place and Urban Area-to-County-Subdivision relationship files. A municipality is `urban` when at least half of its Census entity land area overlaps a 2020 Urban Area, `rural` when no land overlaps, and `unknown` when the overlap is positive but below half or the reference relationship is missing. This is a transparent municipality-level land-overlap rule, not an intuitive metropolitan label. No suburban category is fabricated.
