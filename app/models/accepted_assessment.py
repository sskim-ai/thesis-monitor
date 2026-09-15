from __future__ import annotations

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
)


# V2 deliberately has independent metadata. Importing this module must never make
# the application's legacy SQLModel.metadata.create_all() migrate production.
PERSISTENCE_V2_METADATA = MetaData()


_legacy_assessment_reference = Table(
    "thesisassessment",
    PERSISTENCE_V2_METADATA,
    Column("id", Integer, primary_key=True),
)


canonical_acceptance_receipt_v1 = Table(
    "canonical_acceptance_receipt_v1",
    PERSISTENCE_V2_METADATA,
    Column("acceptance_id", String(68), primary_key=True),
    Column("receipt_contract_version", String(64), nullable=False),
    Column("receipt_hash", String(64), nullable=False, unique=True),
    Column("receipt_status", String(16), nullable=False),
    Column("trusted_issuer_id", String(96), nullable=False),
    Column("generation_id", String(160), nullable=False),
    Column("generation_generated_at", DateTime(timezone=True), nullable=False),
    Column("ticker", String(32), nullable=False),
    Column("thesis_version", Integer, nullable=False),
    Column("assessment_date", Date, nullable=False),
    Column("effective_at", DateTime(timezone=True), nullable=False),
    Column("accepted_at", DateTime(timezone=True), nullable=False),
    Column("source_packet_id", String(200), nullable=False),
    Column("packet_hash", String(64), nullable=False),
    Column("source_evidence_snapshot_identity", Text, nullable=False),
    Column("accepted_payload_contract_version", String(96), nullable=False),
    Column("canonical_serialization_contract", String(96), nullable=False),
    Column("final_composed_candidate_hash", String(64), nullable=False),
    Column("canonical_semantic_audit_contract", String(96), nullable=False),
    Column("canonical_semantic_audit_status", String(16), nullable=False),
    Column("finalization_status", String(16), nullable=False),
    Column("core_immutability_status", String(16), nullable=False),
    Column("core_hash", String(64), nullable=False),
    Column("stance_hash", String(64), nullable=False),
    Column("quarantine_reason_codes", Text, nullable=False),
    UniqueConstraint(
        "trusted_issuer_id",
        "generation_id",
        "ticker",
        name="uq_ca_receipt_issuer_generation_ticker",
    ),
    CheckConstraint("receipt_status = 'ACCEPTED'", name="ck_ca_receipt_accepted"),
    CheckConstraint(
        "canonical_semantic_audit_status = 'PASS'",
        name="ck_ca_receipt_semantic_pass",
    ),
    CheckConstraint("finalization_status = 'PASS'", name="ck_ca_receipt_final_pass"),
    CheckConstraint(
        "core_immutability_status = 'PASS'",
        name="ck_ca_receipt_core_pass",
    ),
    CheckConstraint("quarantine_reason_codes = '[]'", name="ck_ca_receipt_not_quarantined"),
    CheckConstraint("thesis_version > 0", name="ck_ca_receipt_thesis_version"),
)
Index(
    "ix_ca_receipt_ticker_assessment_date",
    canonical_acceptance_receipt_v1.c.ticker,
    canonical_acceptance_receipt_v1.c.assessment_date,
)
Index(
    "ix_ca_receipt_generation_id",
    canonical_acceptance_receipt_v1.c.generation_id,
)


accepted_assessment_v2 = Table(
    "accepted_assessment_v2",
    PERSISTENCE_V2_METADATA,
    Column(
        "acceptance_id",
        String(68),
        ForeignKey("canonical_acceptance_receipt_v1.acceptance_id"),
        primary_key=True,
    ),
    Column("schema_contract_version", String(64), nullable=False),
    Column("source_domain", String(40), nullable=False),
    Column("ticker", String(32), nullable=False),
    Column("thesis_version", Integer, nullable=False),
    Column("assessment_date", Date, nullable=False),
    Column("effective_at_utc", DateTime(timezone=True), nullable=False),
    Column("generation_generated_at_utc", DateTime(timezone=True), nullable=False),
    Column("generation_id", String(160), nullable=False),
    Column("ordering_key_json", Text, nullable=False),
    Column("overall_direction", String(8), nullable=False),
    Column("directional_balance_buy", Numeric(4, 1), nullable=False),
    Column("directional_balance_sell", Numeric(4, 1), nullable=False),
    Column("hold_lean", String(16), nullable=False),
    Column("directional_confidence", String(8), nullable=False),
    Column("canonical_business_delta", String(16), nullable=False),
    Column("canonical_payload_contract_version", String(96), nullable=False),
    Column("canonical_payload_json", Text, nullable=False),
    Column("canonical_payload_sha256", String(64), nullable=False),
    Column("business_thesis_context_json", Text, nullable=False),
    Column("earnings_estimate_context_json", Text, nullable=False),
    Column("market_expectation_context_json", Text, nullable=False),
    Column("valuation_context_json", Text, nullable=False),
    Column("risk_context_json", Text, nullable=False),
    Column("sector_interpretation_json", Text, nullable=False),
    Column("buy_drivers_json", Text, nullable=False),
    Column("sell_drivers_json", Text, nullable=False),
    Column("dominant_evidence_json", Text, nullable=False),
    Column("uncertainty_limit_json", Text, nullable=False),
    Column("core_judgment_json", Text, nullable=False),
    Column("structured_unknowns_json", Text, nullable=False),
    Column("material_anchor_refs_json", Text, nullable=False),
    Column("new_buyer_json", Text, nullable=False),
    Column("holder_json", Text, nullable=False),
    Column("reevaluation_up_json", Text, nullable=False),
    Column("reevaluation_down_json", Text, nullable=False),
    Column("security_basis_provenance_json", Text, nullable=False),
    Column("security_basis_provenance_sha256", String(64), nullable=False),
    UniqueConstraint("generation_id", "ticker", name="uq_accepted_v2_generation_ticker"),
    CheckConstraint(
        "source_domain = 'CANONICAL_MODEL_ACCEPTED'",
        name="ck_accepted_v2_canonical_source",
    ),
    CheckConstraint(
        "overall_direction IN ('BUY', 'HOLD', 'SELL')",
        name="ck_accepted_v2_direction",
    ),
    CheckConstraint(
        "directional_confidence IN ('LOW', 'MEDIUM', 'HIGH')",
        name="ck_accepted_v2_confidence",
    ),
    CheckConstraint(
        "canonical_business_delta IN "
        "('STRENGTHENED', 'UNCHANGED', 'WEAKENED', 'UNRESOLVED')",
        name="ck_accepted_v2_business_delta",
    ),
    CheckConstraint(
        "directional_balance_buy >= 0 AND directional_balance_buy <= 10 "
        "AND directional_balance_sell >= 0 AND directional_balance_sell <= 10 "
        "AND directional_balance_buy + directional_balance_sell = 10",
        name="ck_accepted_v2_balance",
    ),
)
Index(
    "ix_accepted_v2_total_order",
    accepted_assessment_v2.c.ticker,
    accepted_assessment_v2.c.effective_at_utc,
    accepted_assessment_v2.c.generation_generated_at_utc,
    accepted_assessment_v2.c.generation_id,
    accepted_assessment_v2.c.acceptance_id,
)
Index(
    "ix_accepted_v2_ticker_assessment_date",
    accepted_assessment_v2.c.ticker,
    accepted_assessment_v2.c.assessment_date,
)


monitoring_current_state_v2 = Table(
    "monitoring_current_state_v2",
    PERSISTENCE_V2_METADATA,
    Column("ticker", String(32), primary_key=True),
    Column(
        "latest_acceptance_id",
        String(68),
        ForeignKey("accepted_assessment_v2.acceptance_id"),
        nullable=False,
        unique=True,
    ),
    Column("latest_effective_at_utc", DateTime(timezone=True), nullable=False),
    Column("latest_generation_generated_at_utc", DateTime(timezone=True), nullable=False),
    Column("latest_generation_id", String(160), nullable=False),
    Column("latest_ordering_acceptance_id", String(68), nullable=False),
    Column("latest_assessment_date", Date, nullable=False),
    Column("latest_thesis_version", Integer, nullable=False),
    Column("row_version", Integer, nullable=False),
    Column("updated_at_utc", DateTime(timezone=True), nullable=False),
    CheckConstraint("row_version > 0", name="ck_current_v2_row_version"),
)
Index(
    "ix_current_v2_latest_assessment_date",
    monitoring_current_state_v2.c.latest_assessment_date,
)


assessment_source_registry_v2 = Table(
    "assessment_source_registry_v2",
    PERSISTENCE_V2_METADATA,
    Column(
        "legacy_assessment_id",
        Integer,
        ForeignKey("thesisassessment.id"),
        primary_key=True,
    ),
    Column("source_domain", String(40), nullable=False),
    Column("automation_eligible", Boolean, nullable=False),
    Column("classification_contract", String(96), nullable=False),
    Column("classified_at_utc", DateTime(timezone=True), nullable=False),
    CheckConstraint(
        "source_domain IN ('MANUAL_USER_AUTHORED', 'LEGACY_UNVERIFIED')",
        name="ck_source_registry_noncanonical",
    ),
    CheckConstraint("automation_eligible = 0", name="ck_source_registry_no_automation"),
)
Index(
    "ix_source_registry_v2_source_domain",
    assessment_source_registry_v2.c.source_domain,
)


warning_state_v2 = Table(
    "warning_state_v2",
    PERSISTENCE_V2_METADATA,
    Column("warning_identity", String(64), primary_key=True),
    Column("ticker", String(32), nullable=False),
    Column("thesis_version", Integer, nullable=False),
    Column("warning_type", String(96), nullable=False),
    Column("condition_contract_version", String(96), nullable=False),
    Column("condition_identity", String(160), nullable=False),
    Column("state", String(16), nullable=False),
    Column("episode", Integer, nullable=False),
    Column(
        "latest_transition_id",
        String(64),
        ForeignKey("warning_transition_v2.warning_transition_id"),
        nullable=True,
    ),
    Column(
        "latest_observation_acceptance_id",
        String(68),
        ForeignKey("accepted_assessment_v2.acceptance_id"),
        nullable=False,
    ),
    Column("latest_ordering_key_json", Text, nullable=False),
    Column("row_version", Integer, nullable=False),
    CheckConstraint("state IN ('open', 'escalated', 'resolved')", name="ck_warning_state"),
    CheckConstraint("episode > 0", name="ck_warning_episode"),
    CheckConstraint("row_version > 0", name="ck_warning_row_version"),
)
Index("ix_warning_v2_ticker_state", warning_state_v2.c.ticker, warning_state_v2.c.state)
Index(
    "ix_warning_v2_latest_acceptance",
    warning_state_v2.c.latest_observation_acceptance_id,
)


warning_transition_v2 = Table(
    "warning_transition_v2",
    PERSISTENCE_V2_METADATA,
    Column("warning_transition_id", String(64), primary_key=True),
    Column(
        "warning_identity",
        String(64),
        ForeignKey("warning_state_v2.warning_identity"),
        nullable=False,
    ),
    Column("episode", Integer, nullable=False),
    Column("from_state", String(16), nullable=True),
    Column("to_state", String(16), nullable=False),
    Column(
        "triggering_acceptance_id",
        String(68),
        ForeignKey("accepted_assessment_v2.acceptance_id"),
        nullable=False,
    ),
    Column("observation_json", Text, nullable=False),
    Column("transition_reason_version", String(96), nullable=False),
    Column("created_at_utc", DateTime(timezone=True), nullable=False),
    UniqueConstraint(
        "warning_identity",
        "episode",
        "triggering_acceptance_id",
        "transition_reason_version",
        name="uq_warning_transition_v2_event",
    ),
    CheckConstraint("to_state IN ('open', 'escalated', 'resolved')", name="ck_transition_to"),
    CheckConstraint(
        "from_state IS NULL OR from_state IN ('open', 'escalated', 'resolved')",
        name="ck_transition_from",
    ),
)
Index(
    "ix_warning_transition_v2_identity_created",
    warning_transition_v2.c.warning_identity,
    warning_transition_v2.c.created_at_utc,
)


notification_outbox_v2 = Table(
    "notification_outbox_v2",
    PERSISTENCE_V2_METADATA,
    Column("outbox_event_id", String(64), primary_key=True),
    Column("event_kind", String(48), nullable=False),
    Column("source_event_id", String(160), nullable=False),
    Column(
        "acceptance_id",
        String(68),
        ForeignKey("accepted_assessment_v2.acceptance_id"),
        nullable=False,
    ),
    Column("channel", String(48), nullable=False),
    Column("payload_contract_version", String(96), nullable=False),
    Column("payload_json", Text, nullable=False),
    Column("payload_sha256", String(64), nullable=False),
    Column("status", String(16), nullable=False),
    Column("attempt_count", Integer, nullable=False),
    Column("next_attempt_at_utc", DateTime(timezone=True), nullable=False),
    Column("last_error_code", String(96), nullable=True),
    Column("sent_at_utc", DateTime(timezone=True), nullable=True),
    Column("created_at_utc", DateTime(timezone=True), nullable=False),
    UniqueConstraint(
        "source_event_id",
        "channel",
        "payload_contract_version",
        name="uq_outbox_v2_source_channel_payload",
    ),
    CheckConstraint(
        "event_kind IN "
        "('DAILY_SUMMARY_NOTIFICATION', 'MATERIAL_STATE_TRANSITION_NOTIFICATION')",
        name="ck_outbox_v2_event_kind",
    ),
    CheckConstraint(
        "status IN ('pending', 'sending', 'sent', 'retry', 'dead_letter')",
        name="ck_outbox_v2_status",
    ),
    CheckConstraint("attempt_count >= 0", name="ck_outbox_v2_attempt_count"),
)
Index(
    "ix_outbox_v2_pending",
    notification_outbox_v2.c.status,
    notification_outbox_v2.c.next_attempt_at_utc,
)
Index("ix_outbox_v2_acceptance", notification_outbox_v2.c.acceptance_id)


PERSISTENCE_V2_TABLES = (
    canonical_acceptance_receipt_v1,
    accepted_assessment_v2,
    monitoring_current_state_v2,
    assessment_source_registry_v2,
    warning_state_v2,
    warning_transition_v2,
    notification_outbox_v2,
)

PERSISTENCE_V2_TABLE_NAMES = tuple(table.name for table in PERSISTENCE_V2_TABLES)
