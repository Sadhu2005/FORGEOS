from forgeos.core.classifier import FailureClassifier


def test_all_classes() -> None:
    clf = FailureClassifier()
    cases = [
        ("SyntaxError: invalid syntax", "syntax"),
        ("ModuleNotFoundError: No module named 'x'", "dependency"),
        ("FAIL: file is non-empty size=0", "logic"),
        ("ollama unreachable at http://127.0.0.1:11434", "env"),
        ("tool not allowed by role ceo: terminal.execute", "permission"),
        ("timeout after 60s", "timeout"),
        ("something odd happened", "unknown"),
    ]
    for message, expected in cases:
        result = clf.classify(message)
        assert result.failure_class == expected, (message, result)


def test_exit_code_fallback() -> None:
    result = FailureClassifier().classify("failed", exit_code=2)
    assert result.failure_class == "logic"
