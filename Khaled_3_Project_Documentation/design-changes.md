# Changes from the Phase 4 & 5 design

Each change keeps the design's intent. Add every new change here and update the class diagram / ERD for the
final submission (Phase 8). Changes marked **Blueprint** or **Pilot** come from the planned bonus features.

## Class diagram and ERD

| # | Where | Change | Why |
|---|---|---|---|
| 1 | All entities | UUID primary keys kept; weak entities `AssetAttachment` and `AssetTag` get their own UUID plus a unique constraint on (assetId, attachmentNo) / (assetId, tagText) | Django needs a single-column primary key; the partial key is still enforced |
| 2 | `Session` | Implemented as `UserSession`; Django's session framework holds the cookie | Avoids clashing with Django's own `Session` table; our row keeps the activity and status the design needs |
| 3 | `User.passwordHash`, `User.lastLoginAt` | Django's `password` and `last_login` fields | Same data, built-in hashing (Argon2id, NFR-16) |
| 4 | `Role.roleName` (enum `RoleName`) | Free-text `name`, plus `permissions` (new `Permission` entity) and `approval_limit` | **Blueprint**: institutions define their own roles; services check permission codes, not role names |
| 5 | `Department` | Adds `parent` (self-reference) and `unit_type` | **Blueprint**: units form a tree; `RoleAssignment.covers(dept)` includes child units |
| 6 | New `ApprovalRule`, `BlueprintDraft` | New entities in the Blueprint module | **Blueprint**: approval routes and the AI-drafted setup |
| 7 | `Asset` | Adds `serial_number`, `external_ref` | **Pilot**: photo auto-capture reads serial numbers; imported registers keep their own ID |
| 8 | `Asset.estimatedValue` | Defined as the value of one unit | Lots have several units; splitting a lot on transfer keeps the per-unit value correct |
| 9 | New `EmbeddingIndex` | Table owned by Matching that stores pgvector embeddings for assets and requests | Keeps Catalogue and Requests free of AI columns (component diagram rule: a module uses another's interface, never its tables) |
| 10 | `Notification` | Adds `read_at` | In-app unread badge (C8) |
| 11 | `AIInferenceRecord`, `MatchRecommendation` | Add `decision_reason` | Section 9.8 asks for a reason on rejection; the class diagram had no field for it |
| 12 | `ModelVersion` | Adds `config` (JSON) | Stores prompt id and ranking weights with the version (Section 9.2) |
| 13 | `ImpactType` | Adds `VERIFIED_AVOIDED_PURCHASE` | **Pilot**: verified savings are reported separately from estimates |
| 15 | `Transfer` | Adds `replaced_planned_purchase` | **Pilot**: the receiver confirms the transfer replaced a planned purchase, so the dashboard can report verified savings apart from estimates |
| 14 | `Transfer` | `status` gains `CANCELLED` | Figure 7.8 ends the transfer when the reservation is cancelled before dispatch; a status records it |
| 16 | `EmissionFactor`, `SustainabilityImpact` | Add `mass_kg_per_unit` (optional) and `units` | Waste diverted needs a typical mass; `units` lets the dashboard say how many moved units a figure covers |
| 17 | `Notification` | Adds `message_ar` | Notifications are written in English and Arabic when sent, and shown in the reader's language |
| 18 | `MatchResultSet` | `request` becomes optional; adds `query_text` | Find searches (before any request exists) are recorded and explained the same way as request matches |
| 19 | `Asset` | Adds `expected_available_on`, `upcoming_note` | Coming-soon listings (Phase 6). A date, not a new state: Figure 7.5 is unchanged |
| 20 | `AssetQuestion` (new, Catalogue) | Question, answer, asker's unit | Questions on an asset (Phase 7); not a chat |
| 21 | `ImportBatch` (new, Catalogue) | Parsed rows, file hash, result | Bulk CSV registration with preview and one-time import (Phase 8) |
| 22 | `SavedNeed`, `NeedMatch` (new, Matching) | A watched need and its latest match signature | Saved needs and alerts (Phase 5); `SavedNeed.asset` marks interest in a coming-soon item |
| 23 | `NotificationType` | Adds `NEED_MATCH`, `AVAILABILITY`, `ASSET_QUESTION`, `ASSET_ANSWER` | New alerts for Phases 5–7 |

## Behaviour decided in code (the design left it open)

| # | Topic | Decision |
|---|---|---|
| B1 | Condition values | `NEW, GOOD, FAIR, POOR` (best to worst); requests may ask for `ANY`. Confirm or change before data is entered. |
| B2 | Asset state with partly reserved lots | The asset is `RESERVED` only when every available unit is reserved; otherwise it stays `AVAILABLE`, and the reserved count shows the commitment. |
| B3 | Receipt of part of a lot | The received units become a new `Asset` record owned by the receiving department; the original keeps the rest. Both get history events. |
| B4 | Approval steps | One approval step per request (one `ApprovalDecision`, as in the ERD). Blueprint rules decide which role approves. Multi-step routes are future work. |
| B5 | Who approves | The approver needs `request.approve` covering the department that **owns the asset**, within the role's AED limit, and, if a Blueprint rule matches, the rule's role. |
| B6 | Background jobs | A polling `runworker` command instead of a task queue. No Redis/Celery to install for ~200 users. |
| B8 | Screen styling | Our own small design system (`theme.css`) instead of Bootstrap: the approved prototype was built without it, and logical CSS properties give Arabic right-to-left for free. HTMX is shipped in `static/vendor` so labs without internet still work. |
| B7 | Embedding model | `paraphrase-multilingual-MiniLM-L12-v2` (384 dimensions) so Arabic requests can match English listings. **Update (Step 7):** an offline bilingual "lexical" embedder is the default because the model can't be downloaded in our build environment; the real model is one setting away (`EMBEDDING_BACKEND`). |
| B9 | Mandatory specifications | Scored (factor f2, with a size check) instead of a hard filter: free text has no reliable "must have" list. |
| B11 | Sustainable-action advice (Feature 2) | Worked out by fixed rules each time it is shown and **not stored**; `SustainabilityRecommendation` (Figure 7.11) is kept for AI advice with accept/reject. The AI may only re-word the rule result, labelled, and a reply with a number not in the input is discarded |
| B12 | Partial matches | Only the procurement check and saved needs pass `allow_partial`; Find and request matching keep the full-quantity hard rule |
| B10 | Avoided purchase | Value × quantity − transfer cost (the approved prototype's formula), not value × quantity (Phase 5): the more conservative figure. |

## Outside the course scope as written in Phases 1–2

Importing an existing university register (BMC/SAP/Oracle export) is a pilot feature. Phase 1–2 list
integration with official registers as out of scope, so the course version uses test data only; the import
stub in `catalogue/services.py` should be presented as an extension, not as integration with KU systems.
