# Changelog

## Unreleased

### Added

- `Elements` class representing the `nwr` query statement (`Nodes`,
  `Ways` and `Relations` are specialized child classes of `Elements`).
- Filter operations on `Union` and `Difference` derived from the
  `Set` class.
- Nested unions of unions are merged into a single union when the query
  is built.

### Fixed

- Semantically incorrect filter simplification when chaining different
  types of sets.

### Changed

- Removed `QueryStatement` and `BlockStatement` for a generic `Set`
  for better abastraction.
- `out()` doesn't return anything.

## 0.1.1 (2023-08-09)

### Added

- Better test coverage.

### Fixed

- Missing double quotes around CSV separator in query settings.

### Changed

- Removed exception if empty user list in user filter constructor.
- Raise an `UnexpectedCompilationError` instead of a `RuntimeError` on a duplicate variable.

## 0.1.0 (2023-08-08)

Initial release.
