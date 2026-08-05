# Exhaustive external-data pipeline partial-resume checkpoint

**Decision:** `broad_state_whole_corpus_external_data_exhaustive_pipeline_partial_stage_resume_ready`

The residual hosted-search backend transitioned from usable Category A behavior to a Category B global zero-source state. The workflow stopped before URL verification or any later stage.

- Residual rows: **18,689**
- Candidate-bearing searches preserved: **2,847**
- Authoritative bulk resolutions preserved: **2,998**
- Anomalous zero-source outcomes superseded and locked for resume: **12,844**
- Wave-two raw candidates preserved: **91,105**
- Wave-two canonical candidates preserved: **33,003**
- Provisional merged candidates reviewed: **62,796**
- Provisional verification-ready rows: **32,355**

Stage-two review is explicitly provisional and supplies no continuation authority. After the transport returns to Category A and a production probe succeeds, only the locked 12,844-row queue should resume. The successful 2,847 searches and 2,998 bulk resolutions must not be rerun. Candidate review must then be remerged before verification.
