"""Runtime patches for third-party feature-model libraries.

flamapy 2.5.0's ``Constraint.is_single_feature_constraint()`` assumes the root
AST operator is binary and dereferences ``root_op.right`` unconditionally. For a
top-level negation of a compound expression (e.g. ``!(A & B)``) the ``NOT`` node
is unary, so ``root_op.right`` is ``None`` and the method raises
``AttributeError: 'NoneType' object has no attribute 'is_term'``.

fmfactlabel calls this method while computing constraint metrics, so any
uploaded UVL model containing such a constraint makes FactLabel generation fail
(the worker task swallows the error and never stores a FactLabel). We reimplement
the method defensively until the fix lands upstream.

Ref: flamapy.metamodels.fm_metamodel.models.feature_model.is_single_feature_constraint
"""

import logging

logger = logging.getLogger(__name__)


def apply() -> None:
    """Idempotently install the flamapy constraint-classification fix."""
    try:
        from flamapy.core.models.ast import ASTOperation
        from flamapy.metamodels.fm_metamodel.models.feature_model import Constraint
    except Exception:  # pragma: no cover - flamapy internals moved
        logger.warning("flamapy not importable; skipping is_single_feature_constraint patch")
        return

    def is_single_feature_constraint(self) -> bool:
        """True if the constraint is a single feature (``A``) or its negation (``!A``).

        None-safe: a top-level ``NOT`` is unary, so ``root_op.right`` is ``None``.
        """
        root_op = self._ast.root
        if root_op.is_term():
            return True
        if root_op.data == ASTOperation.NOT:
            left, right = root_op.left, root_op.right
            return (left is not None and left.is_term()) or (right is not None and right.is_term())
        return False

    Constraint.is_single_feature_constraint = is_single_feature_constraint
