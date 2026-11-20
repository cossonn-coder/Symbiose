# Live world scaling

- Spatial queries keep a bounds index across successive snapshots. Scene patches identify edited entities. Pose providers identify the entities they move, and socket and parent links carry those updates through attachments. Whole-table replacements and out-of-order reads can rebuild the index from the requested snapshot. A one-off query or a query covering the scene can use a scan.
- Mechanics uses a refittable bounds tree to find candidate contacts, support columns, and clearance distances. Contacts still resolve in the same order. When a collision moves a body or assembly, later contacts can see its corrected bounds. Small, densely overlapping, or unindexable scenes can use the ordered scan. Route queries use the same support and clearance reads.
- Structured patches copy an edited collection once per batch. Tests and subsequent edits see the latest draft. Validation and publication still apply to the whole result, with unchanged branches shared.
- Bare field and trace names use a lookup table built on first use in the snapshot. An ambiguous name still requires `system/name`.

[Rill Spatial's scan and packed query paths](https://github.com/siliconjungle/rill-spatial/blob/f160fb8/README.md) and [Rill State's revision model](https://github.com/siliconjungle/rill-state/tree/829bd2f) informed the spatial index. [Frontier's immutable patch application](https://github.com/siliconjungle/-shapeshift-labs-frontier/blob/2c72dbb/src/apply.ts) informed patch ownership and dirty entity tracking. [Frontier Query](https://github.com/siliconjungle/-shapeshift-labs-frontier-query/tree/ca78eae) informed indexed name resolution. [Ink Lang's guarded dependency tracking](https://github.com/siliconjungle/ink-lang/blob/758fd41b/docs/key-sensitive-access.md) informed when to retain or rebuild a projection.

Ink Studio already uses typed-array terrain A*. Its route costs sample live support, clearance, water, and wear. The route benchmark measures those reads without changing route sampling or search. Frontier's patch-native navigation grids would need a grid authoring or invalidation contract for those fields. Frontier's significance-based scheduling would change which systems advance. Rill's replication and delivery address network workloads. [Frontier Pathfinding](https://github.com/siliconjungle/-shapeshift-labs-frontier-pathfinding/tree/afbde6c) · [Frontier LOD](https://github.com/siliconjungle/-shapeshift-labs-frontier-lod/tree/555f5de)

## Reproduce the benchmark

```sh
git worktree add --detach ../ink-studio-scale-base 4300294
node scripts/benchmark-world-scale.js --baseline=../ink-studio-scale-base --runs=9 --json
```

Use `--only=case,case` to run selected workloads. The benchmark runs a warmup per lane and alternates order in the same process. Each measured run checks the SHA-256 digest of its serialized checkpoint and sampled results against the baseline. Timing includes runtime setup and the workload, with serialization for the comparison outside the timed section.

## Results

Apple M4 Pro, macOS 15.7.4 (Darwin 24.6.0), Node v22.22.1, nine measured runs per lane. Lower time is better. All 17 workloads matched the baseline digest on every run.

| Workload | Baseline median | Updated median | Speedup |
| --- | ---: | ---: | ---: |
| Tiny mechanics, 12 bodies | 3.58 ms | 2.90 ms | 1.23× |
| Fixed town, 512 bodies | 419.00 ms | 51.54 ms | 8.13× |
| Sparse mechanics, 128 bodies | 70.17 ms | 16.03 ms | 4.38× |
| Sparse mechanics, 512 bodies | 1,060.03 ms | 71.01 ms | 14.93× |
| Dense mechanics, 192 bodies | 170.99 ms | 52.54 ms | 3.25× |
| Packed contacts, 256 bodies | 103.51 ms | 101.39 ms | 1.02× |
| 960 support and 960 clearance probes, 512 bodies | 413.72 ms | 47.46 ms | 8.72× |
| First spatial query, 3,500 entities | 9.19 ms | 9.83 ms | 0.94× |
| Scene-wide spatial queries, 3,500 entities | 19.64 ms | 13.13 ms | 1.50× |
| Spatial queries with eight edits per tick, 3,500 entities | 177.50 ms | 58.95 ms | 3.01× |
| Spatial queries with no edits, 3,500 entities | 65.82 ms | 23.32 ms | 2.82× |
| Spatial queries with 64 moving bodies, 64 attachments and 3,500 props | 266.22 ms | 81.64 ms | 3.26× |
| 120 edits against a 4,000-entity manifest | 116.46 ms | 11.35 ms | 10.26× |
| 4,800 bare-name probes over 256 fields | 8.83 ms | 4.51 ms | 1.96× |
| Three walking routes with 256 obstacles | 1,354.87 ms | 39.55 ms | 34.25× |
| Quarry scenario | 288.57 ms | 278.21 ms | 1.04× |
| Watershed simulation | 120.24 ms | 126.40 ms | 0.95× |

The cold spatial query and watershed case were slower by 0.64 ms and 6.16 ms respectively. Their p95s were within 0.50 ms of baseline. The packed-contact case was close to baseline after switching dense rows to a scan. These measurements are for the headless runtime.
