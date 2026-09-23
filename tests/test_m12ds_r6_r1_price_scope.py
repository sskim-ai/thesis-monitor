from pathlib import Path

from scripts import approved_scope_descendants as scope


def test_only_exact_price_basis_migration_is_an_approved_descendant():
    for path in scope.R6_R1_PRICE_BEFORE:
        raw = Path(path).read_bytes()
        assert scope._r6_r1_price_approval(path, raw)['exact_transform_verified']
        assert scope._r6_r1_price_approval(path, raw + b'\n# unapproved change\n') is None
        assert scope._r6_r1_price_approval(path, raw.replace(b'price_basis', b'price_basis_other')) is None


def test_unrelated_path_has_no_migration():
    assert scope._r6_r1_price_transform('app/services/directional_balance_service.py', b'anything') is None
