# Minimal repro: dev-dependency cycle + cfg(test) two-instance break

```console
cargo build -p foo          # passes (lib only)
cargo test  -p foo --test it  # passes (integration test: foo linked once)
cargo test  -p foo          # FAILS: E0277 + "multiple different versions of crate `foo`"
```

`foo`'s own `#[cfg(test)]` unit test consumes a value built by the `fixtures`
dev-dependency, which links the non-`cfg(test)` build of `foo` — a distinct
type instance from the unit-test build. See the article HANDOFF in
`articles/rust-test-fixtures-cfg-test-dev-dep.md`.
