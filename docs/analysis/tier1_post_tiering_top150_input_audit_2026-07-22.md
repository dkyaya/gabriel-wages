# Tier 1 Post-Tiering Top-150 Locked Input Audit

Date: 2026-07-22

Disposition: **PASS — the locked file contains exactly 150 ordinary Tier 1 future-scout targets.**

- Rows: 150
- Tier: {'Tier 1': 150}
- Future eligible: {'true': 150}
- Retry flag: {'false': 150}
- Failure-only flag: {'false': 150}
- Scout status: {'not_scouted': 150}
- Canonical flag: {'false': 150}
- Unique municipality IDs: 150
- Unique Census government IDs: 150; missing: 0
- Known failure-only municipalities present: 0
- Allowed employer identities: {('municipal', 'place'): 150}

Eight selected labels contain `COUNTY` because the authoritative universe classifies them as consolidated `municipal` / `place` employers, not standalone county-government rows: CITY AND COUNTY OF HONOLULU (HI); METRO GOVERNMENT OF LOUISVILLE-JEFFERSON COUNTY (KY); CITY AND COUNTY OF DENVER (CO); METROPOLITAN GOVERNMENT OF NASHVILLE-DAVIDSON COUNTY (TN); URBAN COUNTY GOVERNMENT OF LEXINGTON-FAYETTE (KY); CONSOLIDATED GOVERNMENT OF AUGUSTA-RICHMOND COUNTY (GA); COUNTY OF MACON-BIBB (GA); UNIFIED GOVERNMENT OF WYANDOTTE COUNTY AND KANSAS CITY (KS). Their verification notes prohibit county substitution.

Identity, county context, all requested score components, status fields, source rank, and priority reason are preserved. Added audit-ready scout fields provide exact-employer unit controls without changing the priority score or source files.

## Distribution

- States: AK 1, AL 6, AR 2, AZ 11, CO 9, CT 3, DC 1, FL 15, GA 7, HI 1, IA 4, ID 1, IN 2, KS 4, KY 2, LA 3, MA 9, MD 1, MI 4, MN 4, MO 5, MS 1, NC 8, NE 2, NM 2, NV 4, OH 2, OK 3, OR 3, RI 1, SC 3, SD 1, TN 7, UT 1, VA 7, WA 6, WI 4
- Population: min 70,542; median 196,626; max 1,650,070; missing 0
- Confidence: high 0, medium 0, low 150
- Score: min 75.071; median 75.801; max 78.002
- Source-rank span: 1–156; ordinary Tier 1 ranks are 1–150.

Locked CSV SHA-256: `798d1d1bb2c4c47bb8cdddb3cb929807f86574ca5d029c52875a26aad13824ee`

## State counts

| State | Rows |
|---|---:|
| AK | 1 |
| AL | 6 |
| AR | 2 |
| AZ | 11 |
| CO | 9 |
| CT | 3 |
| DC | 1 |
| FL | 15 |
| GA | 7 |
| HI | 1 |
| IA | 4 |
| ID | 1 |
| IN | 2 |
| KS | 4 |
| KY | 2 |
| LA | 3 |
| MA | 9 |
| MD | 1 |
| MI | 4 |
| MN | 4 |
| MO | 5 |
| MS | 1 |
| NC | 8 |
| NE | 2 |
| NM | 2 |
| NV | 4 |
| OH | 2 |
| OK | 3 |
| OR | 3 |
| RI | 1 |
| SC | 3 |
| SD | 1 |
| TN | 7 |
| UT | 1 |
| VA | 7 |
| WA | 6 |
| WI | 4 |
