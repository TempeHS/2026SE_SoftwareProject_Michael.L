# 🛡️ Bandit SAST Report

## 📊 Summary

| Metric | Value |
| :--- | :--- |
| 📝 Lines of Code Scanned | **1160** |
| 🔴 High Severity | **0** |
| 🟠 Medium Severity | **3** |
| 🔵 Low Severity | **7** |
| 🧮 Total Issues | **10** |

## 🔍 Issues Overview

| # | Severity | Test ID | Issue | Location |
| :-: | :--- | :--- | :--- | :--- |
| 1 | 🟠 MEDIUM | `B608` | Possible SQL injection vector through string-based query construction. | `./main.py:546:12` |
| 2 | 🟠 MEDIUM | `B608` | Possible SQL injection vector through string-based query construction. | `./main.py:554:12` |
| 3 | 🟠 MEDIUM | `B104` | Possible binding to all interfaces. | `./main.py:1342:35` |
| 4 | 🔵 LOW | `B101` | Use of assert detected. The enclosed code will be removed when compiling to optimised byte code. | `./tests/test_main.py:5:4` |
| 5 | 🔵 LOW | `B101` | Use of assert detected. The enclosed code will be removed when compiling to optimised byte code. | `./tests/test_main.py:12:4` |
| 6 | 🔵 LOW | `B101` | Use of assert detected. The enclosed code will be removed when compiling to optimised byte code. | `./tests/test_main.py:16:4` |
| 7 | 🔵 LOW | `B101` | Use of assert detected. The enclosed code will be removed when compiling to optimised byte code. | `./tests/test_main.py:17:4` |
| 8 | 🔵 LOW | `B101` | Use of assert detected. The enclosed code will be removed when compiling to optimised byte code. | `./tests/test_main.py:18:4` |
| 9 | 🔵 LOW | `B101` | Use of assert detected. The enclosed code will be removed when compiling to optimised byte code. | `./tests/test_main.py:23:4` |
| 10 | 🔵 LOW | `B101` | Use of assert detected. The enclosed code will be removed when compiling to optimised byte code. | `./tests/test_main.py:24:4` |

## 📋 Detailed Findings

### 🟠 Issue #1: Possible SQL injection vector through string-based query construction.

- **Severity:** MEDIUM
- **Confidence:** Medium
- **Test ID:** `B608`
- **CWE:** [CWE-89](https://cwe.mitre.org/data/definitions/89.html)
- **Location:** `./main.py:546:12`

```python
545	        rows = conn.execute(
546	            f"SELECT event_id, choice, COUNT(*) AS c FROM huddle_votes "
547	            f"WHERE event_id IN ({placeholders}) GROUP BY event_id, choice",
548	            event_ids,
```

### 🟠 Issue #2: Possible SQL injection vector through string-based query construction.

- **Severity:** MEDIUM
- **Confidence:** Medium
- **Test ID:** `B608`
- **CWE:** [CWE-89](https://cwe.mitre.org/data/definitions/89.html)
- **Location:** `./main.py:554:12`

```python
553	        my_rows = conn.execute(
554	            f"SELECT event_id, choice FROM huddle_votes "
555	            f"WHERE user_id = ? AND event_id IN ({placeholders})",
556	            [user_id, *event_ids],
```

### 🟠 Issue #3: Possible binding to all interfaces.

- **Severity:** MEDIUM
- **Confidence:** Medium
- **Test ID:** `B104`
- **CWE:** [CWE-605](https://cwe.mitre.org/data/definitions/605.html)
- **Location:** `./main.py:1342:35`

```python
1341	    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
1342	    app.run(debug=debug_mode, host="0.0.0.0", port=5000)
```

### 🔵 Issue #4: Use of assert detected. The enclosed code will be removed when compiling to optimised byte code.

- **Severity:** LOW
- **Confidence:** High
- **Test ID:** `B101`
- **CWE:** [CWE-703](https://cwe.mitre.org/data/definitions/703.html)
- **Location:** `./tests/test_main.py:5:4`

```python
4	    )
5	    assert err is None
6
```

### 🔵 Issue #5: Use of assert detected. The enclosed code will be removed when compiling to optimised byte code.

- **Severity:** LOW
- **Confidence:** High
- **Test ID:** `B101`
- **CWE:** [CWE-703](https://cwe.mitre.org/data/definitions/703.html)
- **Location:** `./tests/test_main.py:12:4`

```python
11	    )
12	    assert err is not None
13
```

### 🔵 Issue #6: Use of assert detected. The enclosed code will be removed when compiling to optimised byte code.

- **Severity:** LOW
- **Confidence:** High
- **Test ID:** `B101`
- **CWE:** [CWE-703](https://cwe.mitre.org/data/definitions/703.html)
- **Location:** `./tests/test_main.py:16:4`

```python
15	def test_is_safe_next(app_module):
16	    assert app_module.is_safe_next("/your-huddle") is True
17	    assert app_module.is_safe_next("https://evil.com") is False
```

### 🔵 Issue #7: Use of assert detected. The enclosed code will be removed when compiling to optimised byte code.

- **Severity:** LOW
- **Confidence:** High
- **Test ID:** `B101`
- **CWE:** [CWE-703](https://cwe.mitre.org/data/definitions/703.html)
- **Location:** `./tests/test_main.py:17:4`

```python
16	    assert app_module.is_safe_next("/your-huddle") is True
17	    assert app_module.is_safe_next("https://evil.com") is False
18	    assert app_module.is_safe_next("//evil.com") is False
```

### 🔵 Issue #8: Use of assert detected. The enclosed code will be removed when compiling to optimised byte code.

- **Severity:** LOW
- **Confidence:** High
- **Test ID:** `B101`
- **CWE:** [CWE-703](https://cwe.mitre.org/data/definitions/703.html)
- **Location:** `./tests/test_main.py:18:4`

```python
17	    assert app_module.is_safe_next("https://evil.com") is False
18	    assert app_module.is_safe_next("//evil.com") is False
19
```

### 🔵 Issue #9: Use of assert detected. The enclosed code will be removed when compiling to optimised byte code.

- **Severity:** LOW
- **Confidence:** High
- **Test ID:** `B101`
- **CWE:** [CWE-703](https://cwe.mitre.org/data/definitions/703.html)
- **Location:** `./tests/test_main.py:23:4`

```python
22	    code = app_module.generate_invite_code()
23	    assert len(code) == 6
24	    assert all(c in app_module.INVITE_CODE_ALPHABET for c in code)
```

### 🔵 Issue #10: Use of assert detected. The enclosed code will be removed when compiling to optimised byte code.

- **Severity:** LOW
- **Confidence:** High
- **Test ID:** `B101`
- **CWE:** [CWE-703](https://cwe.mitre.org/data/definitions/703.html)
- **Location:** `./tests/test_main.py:24:4`

```python
23	    assert len(code) == 6
24	    assert all(c in app_module.INVITE_CODE_ALPHABET for c in code)
```
