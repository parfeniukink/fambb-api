"""
this package includes all the tests. ``pytest`` is used as a testing framework.

which philosophy is used for writing tests?
tldr: 5 layered test functions. here is the example of such a test function:

```py
def test_me(fixtures):
    initial = setup_data()
    result = test(initial)
    expected = build_expected(result)

    assert result == expected
```

for sure not all the layers are required and there is no limit yourself in
more complicated scenarios, like next one:

```py
def test_me(fixtures):
    initial = setup_data()

    result1 = test(initial, None)
    result2 = test(initial, result1)  # additional context

    expected1 = build_expected(result)
    expected2 = build_expected(result2)

    assert result1 == expected1
    assert result2 == expected2
```

basically, the 'assertion' part must be separated and be the last one!
the data initiating must go first, and the testing process in the middle.
"""
