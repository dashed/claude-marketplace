# Low-value test patterns, with examples

Each pattern: a weak test, why it is weak, the fix, and what detects it. In the runnable
examples, `BROKEN=1` breaks production the way the weak test cannot see. Each `_weak` test
passes against the broken code and each `_fixed` test fails there. The repository's test suite
runs every `python` block in this file both ways, so the claims stay true. `py` blocks are
illustrations only.

Every runnable example shares this header:

```python
import json
import os
from dataclasses import dataclass
from unittest import mock

import pytest

BROKEN = os.environ.get("BROKEN") == "1"
```

## Table of contents

- [Pins nothing](#pins-nothing)
- [Pins the past](#pins-the-past)
- [Pins its own inputs](#pins-its-own-inputs)
- [Pins implementation](#pins-implementation)
- [Pins one thing twice](#pins-one-thing-twice)
- [Pins less than it claims](#pins-less-than-it-claims)
- [Detector summary](#detector-summary)

## Pins nothing

### A comparison without `assert`

```python
def add(a: int, b: int) -> int:
    return a - b if BROKEN else a + b


def test_add_weak():
    add(1, 2) == 3


def test_add_fixed():
    assert add(1, 2) == 3
```

The result of the comparison is thrown away, so the test asserts nothing. The same miss hides
in a test that only calls the code: it pins "does not raise", nothing more. **Detect**:
`scan_smells.py` `no-assert`, ruff `B015`. An `assert (value, "message")` is always true: ruff
`F631`.

When not raising is the contract — a validator that accepts valid input, a handler that must
swallow a failure — keep the test (`F`) and make the contract visible in its name.

### An expression compared with itself

```python
class Invoice:
    def __init__(self, items: list[int]) -> None:
        self.total = 0 if BROKEN else sum(items)


def test_invoice_total_weak():
    invoice = Invoice([2, 3])
    assert invoice.total == invoice.total


def test_invoice_total_fixed():
    assert Invoice([2, 3]).total == 5
```

Usually a typo for the expected value. **Detect**: `scan_smells.py` `self-compare`; ruff
`PLR0124` covers only a bare name compared with itself.

### A test that only exercises a dependency

```python
@dataclass
class Point:
    x: int
    y: int

    def manhattan(self) -> int:
        return abs(self.x) - abs(self.y) if BROKEN else abs(self.x) + abs(self.y)


def test_point_fields_weak():
    point = Point(3, -4)
    assert (point.x, point.y) == (3, -4)


def test_point_manhattan_fixed():
    assert Point(3, -4).manhattan() == 7
```

`@dataclass` writes `__init__`, so the weak test passes whatever the code you wrote does: it
tests the standard library. The same holds for a test that the ORM saves a plain field, that a
serializer copies one, or that the framework routes a request to a view. Ask what would have to
change for the test to fail. If only the dependency could make it fail, the test belongs to the
dependency: drive the code you wrote instead, or delete the test.

An `isinstance` check on a return value is the same case when a type checker proves that type
on every caller in CI. Keep it when the value crosses a boundary the type checker cannot see:
JSON, a database row, user input, an untyped caller.

Keep a dependency test that pins your configuration of the dependency (a validator, a custom
field, a serializer option you declared), or a dependency behavior your code relies on and the
dependency does not promise. Name the dependency in the test, so that the upgrade that changes
the behavior fails a test that says why. **Detect**: manual.

## Pins the past

### A tombstone for removed code

```py
# Added in the commit that deleted billing/legacy_export.py.
def test_legacy_export_is_gone():
    with pytest.raises(ModuleNotFoundError):
        import billing.legacy_export
```

No change to the live code can make this test fail. The regression it claims to catch is the
module coming back. When the test landed in the commit that removed the module, a revert of that
commit removes the test too. Delete it. The same applies to a test that a moved module is absent
from its old path, or that a deleted function or a dropped flag is gone.

Keep an absence test when the absence is a contract and something could bring the removed thing
back: a dependency banned on purpose that a new requirement could pull in, an insecure endpoint,
a public API removed in a major release. Assert it through the real boundary, and put the reason
in the name or a comment:

```py
def test_reset_link_rejects_get(client):
    # 2.4 removed GET /reset?token=..., which wrote reset tokens to access logs.
    assert client.get("/reset", params={"token": "t"}).status_code == 405
```

When a guard applies only for a while, make it fail when its condition ends, and put the next
step in the message (`libfoo` stands for any dependency with an optional C extension):

```py
def test_libfoo_uses_its_c_extension():
    # libfoo 1.x falls back to pure Python without a warning; 2.x has no fallback.
    if not libfoo.__version__.startswith("1."):
        pytest.fail("libfoo 2 has no fallback: delete this test")
    assert libfoo.compiled
```

**Detect**: manual. An absence assertion (`pytest.raises(ModuleNotFoundError)`, `not hasattr`, a
path that must not exist) is a candidate, not a finding. On a 33,619-test Django application,
14 of the 15 such assertions pinned live behavior (a middleware that must not attach a session,
a service principal that has no email), and the fifteenth guarded a banned dependency. The
history decides. `git log -S '<test name>' --reverse --format='%h %s' -- <file>` lists first the
commit that added the test. If that commit deleted what the test says is gone, the test is a
tombstone.

## Pins its own inputs

### An expected value computed by the code under test

```python
def slug(title: str) -> str:
    return title.lower() if BROKEN else title.lower().replace(" ", "-")


def test_slug_weak():
    expected = slug("Hello World")
    assert slug("Hello World") == expected


def test_slug_fixed():
    assert slug("Hello World") == "hello-world"
```

Whatever `slug` returns, it equals itself. The same flaw hides in snapshot and golden files
regenerated by the code under test and never reviewed. **Detect**: `scan_smells.py`
`repeat-call` (through locals assigned just before the comparison).

### An expected value that repeats the production formula

```python
TAX_PERCENT = 25 if BROKEN else 20


def gross(net_cents: int) -> int:
    return net_cents * (100 + TAX_PERCENT) // 100


def test_gross_weak():
    net = 500
    assert gross(net) == net * (100 + TAX_PERCENT) // 100


def test_gross_fixed():
    assert gross(500) == 600
```

The weak test builds its expected value from the production constant and the production
formula, so a wrong rate moves both sides of the comparison together. A formula copied into the
test also copies its bug. Work the expected value out by hand from the requirement (20% tax on
500 cents is 600) and write the literal.

A computed expected value is a real oracle only when it is independent of the code under test: a
simpler reference implementation (a brute-force search that checks an indexed one), an inverse
(`decode(encode(x)) == x`), or a property that every output must satisfy. **Detect**: manual;
look for expected values that read a production constant or repeat the operators of the
function body.

### A determinism check that never pins a value

```python
def cache_key(user_id: int, page: str) -> str:
    return "" if BROKEN else f"{user_id}:{page}"


def test_cache_key_weak():
    assert cache_key(1, "home") == cache_key(1, "home")


def test_cache_key_fixed():
    assert cache_key(1, "home") == cache_key(1, "home") == "1:home"
    assert cache_key(1, "home") != cache_key(2, "home")
```

A constant function is deterministic. A determinism, idempotency or caching test also pins the
value, or shows that the output changes when the input does. **Detect**: `scan_smells.py`
`repeat-call`.

### A mock that implements the asserted behavior

```python
class Permissions:
    def __init__(self, admins: list[str]) -> None:
        self.admins = set(admins)

    def has(self, user: str, role: str) -> bool:
        return role == "admin" and user in self.admins


def can_delete(user: str, perms: Permissions) -> bool:
    return True if BROKEN else perms.has(user, "admin")


def test_can_delete_weak():
    perms = mock.Mock()
    perms.has.return_value = True
    assert can_delete("alice", perms)


def test_can_delete_fixed():
    perms = Permissions(admins=["alice"])
    assert can_delete("alice", perms)
    assert not can_delete("bob", perms)
```

The mock supplies the answer and the test asserts it back. Use the real collaborator or a fake
with real behavior, and include the case that must be refused. **Detect**: manual.

### A mock that accepts calls the real API rejects

```python
class Client:
    def send(self, message: str) -> None: ...


def notify(client: Client, text: str) -> None:
    if BROKEN:
        client.send(text, retries=3)  # type: ignore[call-arg]
    else:
        client.send(text)


def test_notify_weak():
    client = mock.Mock()
    notify(client, "hi")
    client.send.assert_called_once()


def test_notify_fixed():
    client = mock.create_autospec(Client, instance=True)
    notify(client, "hi")
    client.send.assert_called_once_with("hi")
```

A bare `Mock` accepts any arguments and any attribute, so one mock can stand in for several
APIs and none of them. `create_autospec` (or `mock.patch(..., autospec=True)`) raises
`TypeError` on a call the real signature rejects. **Detect**: manual; search for `Mock()` and
`MagicMock()` without `spec`.

### A fixture that supplies the outcome

```python
class Order:
    def __init__(self, status: str = "new") -> None:
        self.status = status


def mark_paid(order: Order) -> None:
    if not BROKEN:
        order.status = "paid"


def test_mark_paid_weak():
    order = Order(status="paid")
    mark_paid(order)
    assert order.status == "paid"


def test_mark_paid_fixed():
    order = Order()
    mark_paid(order)
    assert order.status == "paid"
```

Start from the state before the behavior. The same flaw: persistence asserted against a store
the path never writes, or callback ordering that the fixture arranges instead of the owner.
**Detect**: manual; compare the fixture's state with the assertion.

### A copied inventory

```python
FORMATS = ("csv", "json")


def export(rows: list[str], fmt: str) -> str:
    if fmt == "csv":
        return ",".join(rows)
    if fmt == "json" and not BROKEN:
        return json.dumps(rows)
    return ""


def test_formats_weak():
    assert FORMATS == ("csv", "json")


def test_formats_fixed():
    exported = {fmt: export(["a", "b"], fmt) for fmt in FORMATS}
    assert exported == {"csv": "a,b", "json": '["a", "b"]'}
```

The literal copy fails on every legitimate addition and never checks that a listed format
works. Exercise what the inventory promises. **Detect**: manual; look for a literal list, tuple,
manifest or `__all__` compared with a production constant.

## Pins implementation

### Private state

```python
class Inventory:
    def __init__(self) -> None:
        self._stock: dict[str, int] = {}

    def receive(self, sku: str, qty: int) -> None:
        self._stock[sku] = qty if BROKEN else self._stock.get(sku, 0) + qty

    def available(self, sku: str) -> int:
        return self._stock.get(sku, 0)


def test_receive_weak():
    inventory = Inventory()
    inventory.receive("a", 2)
    inventory.receive("a", 3)
    assert "a" in inventory._stock


def test_receive_fixed():
    inventory = Inventory()
    inventory.receive("a", 2)
    inventory.receive("a", 3)
    assert inventory.available("a") == 5
```

The weak test reads a private attribute. It fails when `Inventory` keeps a running total or moves
stock to a database, although the behavior stays the same. It passes when `receive` overwrites
the stock instead of adding to it. Assert through the API that callers use.

**Detect**: ruff `SLF001` lists every private name read outside its class. It is a triage
list, not a verdict. It reported 320 sites in the test suites of requests, httpx, attrs, flask,
rich and click, and 1,467 on the 33,619-test Django application. Three kinds of site share the
rule:

- private state: rich's `_spans`, requests' `_body_position`, httpx's `_pool`;
- underscore names that are public by contract: Django's `_meta` (121 of the 1,467 sites),
  werkzeug's `_get_current_object` (in flask's tests);
- private modules that a suite tests on purpose: `click._termui_impl` (56 sites).

Remove the second kind with
`--config 'lint.flake8-self.extend-ignore-names = ["_meta", "_get_current_object"]'`. Then
apply the refactor check from the authoring gate to each remaining site.

### Call shapes of private helpers

```py
def test_register_calls_normalize():
    with mock.patch("app.users._normalize", wraps=_normalize) as normalize:
        register(" A@B.io ", store)
    normalize.assert_called_once_with(" A@B.io ")
```

Inlining `_normalize`, or normalizing in the model instead, breaks this test while behavior
stays the same, and the real boundary (`register` stores `a@b.io`) already covers the contract.
Assert the stored result instead. **Detect**: the refactor check in the authoring gate; search
for `assert_called*` on private names.

### Source and string greps

```py
def test_client_uses_timeout():
    assert "timeout=" in inspect.getsource(client.fetch)
```

A rename or a refactor into a helper breaks it; a timeout of `0` passes it. Drive `fetch`
against a slow fake and assert the timeout error. Keep source inspection only when the source
text is the contract — generated code, a user-facing key or path — and it survives an
identifier rename. **Detect**: `scan_smells.py` `reads-source`.

### Tests that keep test-only code alive

```py
def test_reset_clears_cache():
    cache.set("k", 1)
    cache._reset_for_tests()
    assert cache.get("k") is None
```

`_reset_for_tests` exists for the test suite, and this test exists for `_reset_for_tests`.
Delete both; isolate state with a fixture that builds a fresh cache. **Detect**:
`find_seams.py`.

## Pins one thing twice

### Two tests, one body — and the missing test behind them

```python
def decode(data: bytes, encoding: str | None = None) -> str:
    if encoding and not BROKEN:
        return data.decode(encoding)
    return data.decode("utf-8", errors="replace")


def test_decode_default():
    assert decode("é".encode()) == "é"


def test_decode_explicit_encoding_weak():
    assert decode("é".encode()) == "é"


def test_decode_explicit_encoding_fixed():
    assert decode("é".encode("latin-1"), encoding="latin-1") == "é"
```

The second test was copied from the first and never got its distinguishing input, so the
explicit-encoding branch has no test. Real cases: httpx `b5addb6`
`test_client_decode_text_using_explicit_encoding`, flask `d73fa1c`
`test_teardown_request_handler_debug_mode`. Give the copy its input (`F`); delete it only when
the name promised nothing distinct (`D`). **Detect**: `scan_smells.py` `dup-body`. Bodies that
differ by one literal are parametrization candidates for test-sloc-cut, not duplicates.

## Pins less than it claims

### A negative control that passes for an unrelated reason

```python
def withdraw(balance: int, amount: int) -> int:
    if not isinstance(amount, int):
        raise ValueError("amount must be an int")
    if amount > balance and not BROKEN:
        raise ValueError("insufficient funds")
    return balance - amount


def test_overdraw_weak():
    with pytest.raises(ValueError):
        withdraw(10, 20.0)  # type: ignore[arg-type]


def test_overdraw_fixed():
    with pytest.raises(ValueError, match="insufficient funds"):
        withdraw(10, 20)
```

The type guard raises first, so the balance guard is never reached. Pin the guard with
`match=` (or a specific exception type), and use input that only the named guard rejects.
**Detect**: ruff `PT011` for broad types without `match=`; manual for a guard that raises a
specific type too.

### Setup inside the `raises` block

```python
def load(text: str) -> dict[str, str]:
    if not text:
        raise ValueError("empty config")
    return dict(line.split("=", 1) for line in text.splitlines())


def parse_port(config: dict[str, str]) -> int:
    port = int(config["port"])
    if not BROKEN and not 0 < port < 65536:
        raise ValueError("port out of range")
    return port


def test_port_range_weak():
    with pytest.raises(ValueError):
        config = load("")
        parse_port(config)


def test_port_range_fixed():
    config = load("port=70000")
    with pytest.raises(ValueError, match="port out of range"):
        parse_port(config)
```

`load("")` raises before `parse_port` runs. Keep only the call under test inside the block.
**Detect**: ruff `PT012`.

### A capability test that restates a flag

```py
def test_webhook_supports_retries():
    assert WebhookSender.supports_retries is True
```

The flag is declared one line from where it is read. Exercise the promise instead: a transport
that fails once, then succeeds, and an assertion that the webhook arrived. **Detect**: manual.

## Detector summary

| Pattern | Detector |
|---|---|
| assertion-free test, comparison without `assert` | `scan_smells.py no-assert`, ruff `B015` |
| `assert` on a tuple | ruff `F631` |
| expression compared with itself | `scan_smells.py self-compare`, ruff `PLR0124` (bare names) |
| expected value from the code under test, value-free determinism check | `scan_smells.py repeat-call` |
| two tests with one body | `scan_smells.py dup-body` |
| source or string grep | `scan_smells.py reads-source` |
| broad `pytest.raises`, setup inside the block | ruff `PT011`, `PT012` |
| assertion inside `except` (passes when nothing raises) | ruff `PT017` |
| test-only production code | `find_seams.py` |
| private state read from outside its class | ruff `SLF001` (a triage list) |
| absence assertion | `rg` for `pytest.raises(ModuleNotFoundError)` and `not hasattr(` gives candidates; the history decides whether one is a tombstone |
| dependency-only test, expected value that repeats the formula, mock implements the behavior, bare mocks, outcome in the fixture, copied inventory, private call shapes, restated flags, names that overpromise | manual, with the ledger |
