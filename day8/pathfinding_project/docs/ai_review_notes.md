# AI Review Notes

## Task 1 — Data-format review

The two-file format contains enough information for shortest-path computation
and map visualisation:

- `Node_Info.txt` stores the node ID, coordinates, building type, and name.
- `Graph_Path.txt` stores the edge ID, endpoint node IDs, and path distance.
- Blank lines and lines beginning with `#` are ignored.
- Duplicate node IDs and edge IDs are rejected.
- An edge that refers to an unknown node is rejected.
- Negative distances are rejected because Dijkstra's algorithm requires
  non-negative edge costs.
- Paths are treated as undirected.
- Coordinates are used only for drawing. `Distance` is used for pathfinding.

A remaining limitation is that names cannot contain spaces under the supplied
format, so underscores are used instead.

## Task 2 — AI-generated test maps

Three additional map pairs are included under `docs/test_maps/`:

1. `connected` — a small normal connected graph.
2. `disconnected` — contains an unreachable node.
3. `equal_paths` — contains two valid shortest paths with the same distance.

These maps help confirm that the program is data-driven rather than hardcoded
to the main sample map.

## Task 3 — Corner-case requests

| Start | End | Expected behaviour | Why it matters |
|---|---:|---|---|
| 0 | 2 | Return `0 → 1 → 2`, distance 300 | Normal shortest path |
| 2 | 2 | Return `[2]`, distance 0 | Start equals end |
| 99 | 2 | Show invalid start-node message | Invalid input |
| 0 | 99 | Show invalid end-node message | Invalid input |
| 0 | 5 | Show that no path exists | Disconnected node |
| 0 | 3 | Return the lowest-distance valid route | Multiple choices |
| 0 | 0 | Return one node and zero cost | Boundary behaviour |

## Task 4 — Authentication review

- Public users can open `/` and run pathfinding without logging in.
- All node and path editing routes use the `editor_required` decorator.
- Unauthenticated edit requests are redirected to the login page.
- The editor password is read from an environment variable rather than shown
  in the interface.
- Failed login attempts show a clear error.
- Every successful edit is written back to the map text files.

For production use, the system would also need password hashing, CSRF
protection, rate limiting, HTTPS, secure cookies, and proper user accounts.
The current mechanism is intentionally simple for the lab.

## Task 5 — Test and verification review

The automated tests check real behaviour:

- normal shortest path;
- start equals end;
- invalid start node;
- invalid end node;
- disconnected destination;
- equal-distance paths;
- public access without login;
- public pathfinding without login;
- unauthorised editing rejection;
- incorrect password rejection;
- authorised editing.

A successful test run proves that these configured behaviours passed for the
tested inputs. It does not prove that every possible map, browser, concurrency
case, or security threat has been covered.
