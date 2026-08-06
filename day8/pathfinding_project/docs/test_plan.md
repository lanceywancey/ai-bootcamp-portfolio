# Verification Test Plan and Results

> Note: The automated edge-case tests use the controlled test map defined in
> `tests/conftest.py`, not the main 16-node map in the `data` folder.

| Test | Input | Expected | Actual | Result |
|---|---|---|---|---|
| Normal shortest path | Start 0, end 2 | `0 → 1 → 2`, distance 300 | Correct path and distance returned | PASS |
| Start equals end | Start 2, end 2 | `[2]`, distance 0 | `[2]`, distance 0 | PASS |
| Invalid start | Start 99, end 2 | Invalid-start error | Invalid-start error raised | PASS |
| Invalid end | Start 0, end 99 | Invalid-end error | Invalid-end error raised | PASS |
| Disconnected destination | Start 0, end 5 | No-path error | No-path error raised | PASS |
| Equal shortest paths | Start 0, end 3 | Valid shortest path, distance 2 | Valid route returned, distance 2 | PASS |
| Public map | GET `/` | HTTP 200 | HTTP 200 | PASS |
| Public pathfinding | POST `/` without login | Correct route displayed | Correct route displayed | PASS |
| Unauthorised edit | POST editor route without login | Redirect to login | Redirected to login | PASS |
| Wrong password | Incorrect password | HTTP 401 and error | HTTP 401 and error shown | PASS |
| Authorised edit | Correct password and add node | Node saved | Node successfully saved | PASS |