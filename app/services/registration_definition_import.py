"""Selective atomic import into the existing registry, never an eligibility grant.

The caller owns the approved database connection and private donor capture.
There is no endpoint, automatic connection, provider call, or startup hook here.
"""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json

from app.services.minimal_class_c_export import COLUMNS, MODELS


WATCH_DEFINITION_FIELDS = (
    'ticker', 'company_name', 'exchange', 'issuer_type', 'ordinary_share_identifier',
    'adr_ratio', 'adr_currency', 'underlying_currency', 'notes',
    'registration_requested_at', 'created_at',
)


def _digest(value):
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
    return hashlib.sha256(raw).hexdigest()


def _logical(table, row):
    # Validate original values; model defaults must not fabricate absent fields.
    if set(row) != set(COLUMNS[table]):
        raise ValueError('registration_import_exact_columns_required')
    try:
        model = MODELS[table].model_validate(row)
    except ValueError:
        raise ValueError('registration_import_original_field_type_invalid') from None
    value = model.model_dump(mode='json')
    for field in value:
        parsed = getattr(model, field)
        if isinstance(parsed, datetime):
            value[field] = parsed.replace(tzinfo=parsed.tzinfo or timezone.utc).astimezone(timezone.utc).isoformat()
    value.pop('id')
    return value


def _key(table, row):
    return (row['ticker'], row['version']) if table == 'investmentthesis' else (row['ticker'],)


def prepare_registration_definitions(rows, *, subjects, max_versions_per_subject):
    """Prepare only original definitions, preserving all permitted Thesis versions."""
    if (not subjects or len(set(subjects)) != len(subjects) or len(subjects) > 100
            or type(max_versions_per_subject) is not int or not 1 <= max_versions_per_subject <= 100):
        raise ValueError('registration_import_bounded_subjects_and_versions_required')
    if set(rows) != set(MODELS):
        raise ValueError('registration_import_exact_four_tables_required')
    target = set(subjects)
    prepared = {table: [] for table in MODELS}
    indices = {}
    for table in MODELS:
        records = rows[table]
        limit = len(subjects) * (max_versions_per_subject if table == 'investmentthesis' else 1)
        if len(records) > limit or any(row.get('ticker') not in target for row in records):
            raise ValueError('registration_import_source_scope_exceeded')
        if len({_key(table, row) for row in records}) != len(records):
            raise ValueError('registration_import_duplicate_source_key')
        if (any(type(row.get('id')) is not int or row['id'] < 1 for row in records)
                or len({row['id'] for row in records}) != len(records)):
            raise ValueError('registration_import_original_record_ids_required')
        if {row['ticker'] for row in records} != target:
            raise ValueError('registration_import_missing_original_definition')
        indices[table] = {row['ticker']: row for row in records}
        for original in records:
            logical = _logical(table, original)
            if table == 'watchlistitem':
                # Drop old onboarding receipts/activation, not user definitions.
                definition = {field: logical[field] for field in WATCH_DEFINITION_FIELDS}
                item = MODELS[table].model_validate(dict(definition, active=False,
                    monitoring_requested=logical['monitoring_requested'], production_eligible=False,
                    onboarding_state='PENDING_ONBOARDING'))
                logical = _logical(table, item.model_dump(mode='json'))
            prepared[table].append(dict(logical, id=original['id']))
    for ticker in subjects:
        item, security, company = (indices[table][ticker]
            for table in ('watchlistitem', 'securitymaster', 'company'))
        if (not item['monitoring_requested'] or not security['canonical_security_id']
                or not security['canonical_company_id']
                or item['exchange'] != security['exchange'] or item['exchange'] != company['exchange']):
            raise ValueError('registration_import_original_identity_conflict')
        theses = [row for row in prepared['investmentthesis'] if row['ticker'] == ticker]
        active = [row for row in theses if row['status'] == 'active']
        if (len(active) != 1 or not active[0]['core_thesis'].strip()
                or any(type(row['version']) is not int or row['version'] < 1 for row in theses)
                or active[0]['version'] != max(row['version'] for row in theses)):
            raise ValueError('registration_import_active_thesis_history_invalid')
    security_ids = [row['canonical_security_id'] for row in prepared['securitymaster']]
    if len(set(security_ids)) != len(security_ids):
        raise ValueError('registration_import_duplicate_security_identity')
    return prepared


def _read_target(connection, prepared, subjects):
    marks = ','.join('?' for _ in subjects)
    result = {}
    for table, columns in COLUMNS.items():
        fields = ','.join(f'"{column}"' for column in columns)
        where, parameters = f'ticker IN ({marks})', tuple(subjects)
        if table == 'securitymaster':
            security_ids = tuple(row['canonical_security_id'] for row in prepared[table])
            where += ' OR canonical_security_id IN (' + ','.join('?' for _ in security_ids) + ')'
            parameters += security_ids
        limit = len(prepared[table]) + len(subjects) + 1
        cursor = connection.execute(f'SELECT {fields} FROM "{table}" WHERE {where} ORDER BY ticker,id LIMIT ?',
                                    (*parameters, limit))
        records = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
        if len(records) >= limit or any(row['ticker'] not in subjects for row in records):
            raise ValueError('registration_import_target_scope_or_unique_conflict')
        if len({_key(table, row) for row in records}) != len(records):
            raise ValueError('registration_import_target_duplicate_key')
        result[table] = records
    return result


def import_registration_definitions(connection, rows, *, subjects,
                                    max_versions_per_subject, enabled=False):
    """One BEGIN IMMEDIATE/COMMIT; exact match is NOOP, mismatch rolls back.

    `enabled` is an ordinary execution switch, not permission issuance. The
    caller must already hold the explicit task read/write approval. Destination
    IDs are allocated by SQLite; donor IDs are recorded only in the mapping.
    """
    if enabled is not True:
        raise ValueError('registration_import_default_off')
    prepared = prepare_registration_definitions(rows, subjects=subjects,
        max_versions_per_subject=max_versions_per_subject)
    if connection.in_transaction:
        raise ValueError('registration_import_owns_whole_transaction_required')
    prepared = deepcopy(prepared)
    mappings, inserted = [], Counter()
    connection.execute('BEGIN IMMEDIATE')
    try:
        marks = ','.join('?' for _ in MODELS)
        trigger = connection.execute(
            f"SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name IN ({marks}) LIMIT 1",
            tuple(MODELS)).fetchone()
        if trigger is not None:
            raise ValueError('registration_import_target_triggers_require_review')
        target = _read_target(connection, prepared, subjects)
        for table, records in prepared.items():
            existing = {_key(table, row): row for row in target[table]}
            keys = {_key(table, row) for row in records}
            if set(existing) - keys:
                raise ValueError('registration_import_unexpected_existing_version')
            for row in records:
                old = existing.get(_key(table, row))
                if old is not None and _logical(table, old) != _logical(table, row):
                    raise ValueError('registration_import_existing_record_mismatch')
        for table, records in prepared.items():
            existing = {_key(table, row): row for row in target[table]}
            columns = tuple(column for column in COLUMNS[table] if column != 'id')
            fields, marks = ','.join(f'"{c}"' for c in columns), ','.join('?' for _ in columns)
            for row in records:
                old = existing.get(_key(table, row))
                if old is None:
                    cursor = connection.execute(f'INSERT INTO "{table}" ({fields}) VALUES ({marks})',
                        tuple(row[column] for column in columns))
                    new_id = cursor.lastrowid
                    inserted[table] += 1
                else:
                    new_id = old['id']
                mappings.append(dict(table=table, ticker=row['ticker'],
                    version=row.get('version'), source_id=row['id'], destination_id=new_id,
                    status='INSERTED_PENDING' if old is None else 'EXACT_NOOP',
                    original_definition_sha256=_digest(_logical(table, row))))
        after = _read_target(connection, prepared, subjects)
        for table, records in prepared.items():
            expected = {_key(table, row): _logical(table, row) for row in records}
            actual = {_key(table, row): _logical(table, row) for row in after[table]}
            if actual != expected:
                raise ValueError('registration_import_transaction_readback_mismatch')
        connection.execute('COMMIT')
    except BaseException:
        if connection.in_transaction:
            connection.execute('ROLLBACK')
        raise
    return dict(contract='original-model-registration-definition-import-v1',
        subjects=list(subjects), inserted=dict(inserted), inserted_rows=sum(inserted.values()),
        mappings=mappings, SELECT=9, commits=1, updates=0, deletes=0,
        activation_granted=False, source_or_economic_grant=False, private_definitions_exported=False)
