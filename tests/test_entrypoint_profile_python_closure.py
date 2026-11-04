"""C profiler rows are not inputs to the Python runtime closure proof."""

import cProfile


def test_disabling_builtin_rows_preserves_python_function_membership():
    def inner():
        return sum(range(20))

    def outer():
        return inner()

    memberships = []
    for builtins in (True, False):
        profile = cProfile.Profile(builtins=builtins)
        assert profile.runcall(outer) == 190
        memberships.append(
            {row.code for row in profile.getstats() if not isinstance(row.code, str)}
        )
    assert memberships[0] == memberships[1] == {outer.__code__, inner.__code__}
