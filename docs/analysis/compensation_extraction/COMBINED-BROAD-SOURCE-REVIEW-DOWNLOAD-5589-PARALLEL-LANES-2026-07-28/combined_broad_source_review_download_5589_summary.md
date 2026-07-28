# Combined broad source-review/download summary

Decision: `combined_broad_source_review_download_5589_completed_pdf_readiness_ready`.

Four isolated, checkpointed workers processed all 5,589 locked metadata leads in the required 1,397 / 1,397 / 1,397 / 1,398 lane split. Starts were staggered at T+0, T+8, T+16, and T+24 with controlled overlap. All four lanes completed and have zero remaining rows.

The coordinator retained 4,961 unique local source files: 3,980 PDFs, 941 HTML files, and 40 other supported documents. Retained bytes total 12,475,949,771. It detected and routed out 243 redundant file hashes plus one pre-identified canonical-locator duplicate. Five files exceeded the 75 MB pass cap. Transport or current-GET availability blocked 299 rows, 65 rows were weak/generic-navigation cases, 11 rows ended in download error, and four had unsupported content types. Retained plus excluded/deferred reconciles exactly to 5,589.

The retained set spans 49 states, all four Census regions, and 2,611 municipalities. Exact `cba` hints account for 672 retained files (13.55%); 4,289 retained files carry non-CBA or mixed-family hints. Leading retained source-family hints are agenda packets/minutes (993), exact CBAs (672), budget/pay plans (641), wage schedules (562), mixed compensation/classification/wage-schedule hints (341), MOUs/memoranda (267), mixed CBA/budget-pay-plan hints (261), other local-government pay policy (249), and salary ordinances (163). These are operational metadata distributions, not prevalence or evidence claims.

The files remain unparsed for evidence, unrendered, un-OCRed, unextracted, unrated, uningested, uncodified, non-causal, and outside global analysis readiness. No wage-gap calculation, regression, treatment-effect estimate, national/population-prevalence claim, or final causal claim was produced. The next recommended task is a separately authorized bounded PDF/text-layer readiness pass over the unique retained local files, using their committed paths, sizes, and SHA-256 hashes without URL access or redownload.
