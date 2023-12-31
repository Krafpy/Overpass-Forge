# Changelog

## 0.4.3 (2023-09-01)

### Added

- `map_to_area` wrapper with `AsAreas` object.

### Changed

- Moved `out` from `Statement` to `Set` only.

## 0.4.2 (2023-08-25)

### Changed

- Enforced return type on query methods.

### Fixed

- Overloaded `filter` methods on derived classes of `Set`
  accept string arguments.

## 0.4.1 (2023-08-25)

### Changed

- `OverlappingAreas` inherit from `Areas`.

## 0.4.0 (2023-08-25)

### Added

- Direct methods for elements retrieval within areas.
- Raw string filter expressions in set's `filter` method.

## 0.3.0 (2023-08-17)

### Added

- Added recursed up (relations) and down (relations) sets
  (`>`, `>>`, `<`, `<<`).
- Added overlapping areas statement (*is_in*).

## 0.2.0 (2023-08-16)

### Added

- `Elements` class representing the `nwr` query statement (`Nodes`,
  `Ways` and `Relations` are specialized child classes of `Elements`).
- Filter operations on `Union` and `Difference` derived from the
  `Set` class.
- Nested unions of unions are merged into a single union when the query
  is built.
- Intersection using the multiplication operator.

### Fixed

- Semantically incorrect filter simplification when chaining different
  types of sets.

### Changed

- Removed `QueryStatement` and `BlockStatement` for a generic `Set`
  for better abastraction.
- `out()` doesn't return anything.
- Renamed `Intersection` filter to `Intersect`.

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
