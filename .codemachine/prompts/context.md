# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I3.T2",
  "iteration_id": "I3",
  "iteration_goal": "Real-Time WebSocket Communication & Frontend Foundation",
  "description": "Update mock vehicle connector from I2.T5 to simulate streaming responses (multiple response chunks for single command). For command \"ReadDTC\", generate 2-3 response chunks published sequentially with delays: chunk 1 (DTC P0420), delay 0.5s, chunk 2 (DTC P0171), delay 0.5s, final chunk (status: complete with is_final=true). For \"ReadDataByID\", simulate progressive data streaming. Each chunk published to Redis as separate event with incrementing sequence_number. Update final chunk to set command status to `completed`. Write unit tests in `backend/tests/unit/test_vehicle_connector.py` verifying multi-chunk generation and timing.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Requirements specify \"streaming responses\"; Architecture Blueprint Section 3.7 (Communication Patterns).",
  "target_files": [
    "backend/app/connectors/vehicle_connector.py",
    "backend/tests/unit/test_vehicle_connector.py"
  ],
  "input_files": [
    "backend/app/connectors/vehicle_connector.py"
  ],
  "deliverables": "Enhanced mock connector with multi-chunk streaming; unit tests verifying streaming behavior.",
  "acceptance_criteria": "Command \"ReadDTC\" generates 3 response chunks (2 DTCs + final status); Each chunk has incrementing sequence_number (1, 2, 3); Final chunk has is_final=true; Chunks published with ~0.5 second intervals (verify timing in tests); WebSocket client (from I3.T1) receives all chunks in correct order; Unit tests verify: correct number of chunks, sequence_number increments, timing delays; Test coverage maintained ≥80%; No linter errors",
  "dependencies": [
    "I3.T1"
  ],
  "parallelizable": false,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: Streaming Response Requirements (from Task Description)

```markdown
The task requires implementing multi-chunk streaming responses for SOVD commands. This simulates real-world scenarios where vehicle diagnostic responses arrive progressively rather than all at once.

**Key Requirements:**
- **ReadDTC Command**: Must generate 2-3 response chunks:
  - Chunk 1: First DTC (P0420) with sequence_number=1
  - Chunk 2: Second DTC (P0171) with sequence_number=2
  - Chunk 3: Final status with sequence_number=3 and is_final=true
- **Timing**: ~0.5 second delays between chunks
- **Redis Events**: Each chunk published as separate event to `response:{command_id}` channel
- **Status Update**: Final chunk triggers command status change to "completed"
```

### Context: WebSocket Real-Time Communication Pattern (from I3.T1)

```markdown
The WebSocket endpoint (already implemented in I3.T1) subscribes to Redis Pub/Sub channels and forwards events to clients in real-time. The vehicle connector must publish events in the correct format:

**Event Format:**
{
  "event": "response",
  "command_id": "uuid",
  "response_id": "uuid",
  "response_payload": {...},
  "sequence_number": 1,
  "is_final": false
}

**Status Event Format (Final):**
{
  "event": "status",
  "command_id": "uuid",
  "status": "completed",
  "completed_at": "2025-10-28T10:00:01.5Z"
}
```

### Context: Current Implementation State (from I3.T1)

```markdown
Task I3.T1 has been completed successfully, which means:
- WebSocket endpoint is fully functional at `/ws/responses/{command_id}`
- JWT authentication is working
- Redis Pub/Sub subscription and event forwarding is operational
- WebSocket clients can receive real-time events
- Multiple concurrent clients are supported
- Proper cleanup and resource management is in place

The vehicle connector currently publishes a SINGLE response chunk per command. This task requires enhancing it to publish MULTIPLE chunks with proper sequencing and timing.
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

#### **File:** `backend/app/connectors/vehicle_connector.py` (391 lines - REQUIRES MODIFICATION)
   - **Summary:** Current mock vehicle connector publishes a single response chunk per command with sequence_number=1 and is_final=True (lines 216-222, 230-241).
   - **Current Behavior:**
     - Single network delay simulation: `await asyncio.sleep(random.uniform(0.5, 1.5))` (lines 168-175)
     - Single response generation per command (lines 186-206)
     - Single response record creation with sequence_number=1, is_final=True (lines 216-222)
     - Single Redis event publication (lines 230-252)
     - Status update to "completed" immediately after single response (lines 253-286)
   - **CRITICAL MODIFICATION REQUIRED:**
     - **You MUST refactor the `execute_command()` function** to support multi-chunk streaming
     - **You MUST change the response generation logic** from single-chunk to multi-chunk
     - **You MUST implement a loop** to generate and publish multiple chunks with delays between them
     - **You MUST increment sequence_number** for each chunk (1, 2, 3, ...)
     - **You MUST set is_final=True** only on the last chunk
     - **You MUST publish separate Redis events** for each chunk

#### **File:** `backend/app/repositories/response_repository.py` (70 lines - READY TO USE)
   - **Summary:** Repository for creating and retrieving command response records from database.
   - **Key Function:** `create_response(db, command_id, response_payload, sequence_number, is_final)` (lines 12-45)
     - Creates a new response record with specified sequence_number
     - Supports is_final flag for marking final chunks
     - Handles UNIQUE constraint on (command_id, sequence_number)
   - **Recommendation:** You SHOULD call this function multiple times (once per chunk) with incrementing sequence_numbers
   - **Note:** The function already supports the multi-chunk pattern - no changes needed

#### **File:** `backend/tests/unit/test_vehicle_connector.py` (393 lines - REQUIRES EXPANSION)
   - **Summary:** Existing unit tests for mock vehicle connector covering single-chunk responses.
   - **Current Coverage:**
     - Response generation tests (lines 17-88)
     - Single-chunk execution tests for ReadDTC, ClearDTC, ReadDataByID (lines 91-348)
     - Error handling tests (lines 349-393)
   - **MODIFICATION REQUIRED:**
     - **You MUST add new test methods** to verify multi-chunk streaming behavior
     - **You MUST test timing delays** between chunks (use time mocking)
     - **You MUST verify sequence_number increments** correctly
     - **You MUST verify is_final flag** is only set on last chunk
     - **You MUST verify Redis events** are published for each chunk
   - **Tip:** Existing tests use extensive mocking patterns - follow the same approach for new tests

### Implementation Tips & Notes

#### **Tip 1: Multi-Chunk Response Generation Strategy**

You have two architectural options for implementing multi-chunk responses:

**Option A: Generate All Chunks Upfront (RECOMMENDED)**
- Generate complete response data at the start
- Split it into chunks
- Publish chunks sequentially with delays
- **Advantage:** Simpler to implement, easier to test, predictable behavior
- **Example for ReadDTC:**
  ```python
  # Generate all DTCs
  all_dtcs = [
      {"dtcCode": "P0420", "description": "...", ...},
      {"dtcCode": "P0171", "description": "...", ...},
  ]
  # Chunk 1: First DTC
  chunk_1_payload = {"dtcs": [all_dtcs[0]], ...}
  # Chunk 2: Second DTC
  chunk_2_payload = {"dtcs": [all_dtcs[1]], ...}
  # Chunk 3: Final status
  chunk_3_payload = {"status": "complete", "totalDtcs": 2, ...}
  ```

**Option B: Progressive Generation**
- Generate each chunk on-demand
- More realistic simulation of real vehicle behavior
- **Disadvantage:** More complex, harder to test timing

**RECOMMENDATION:** Use Option A for this MVP implementation. It's simpler and meets all acceptance criteria.

#### **Tip 2: Refactoring Strategy**

The current `execute_command()` function is ~230 lines. To implement multi-chunk streaming, you should:

1. **Extract a helper function** `_publish_response_chunk()` that:
   - Creates response record in database
   - Publishes Redis event
   - Handles logging
   - Takes sequence_number and is_final as parameters

2. **Extract a helper function** `_generate_streaming_chunks()` that:
   - Takes command_name and command_params
   - Returns list of (response_payload, delay) tuples
   - Example: `[(chunk1_payload, 0.5), (chunk2_payload, 0.5), (chunk3_payload, 0)]`

3. **Update main flow** to:
   ```python
   chunks = _generate_streaming_chunks(command_name, command_params)
   for seq_num, (payload, delay) in enumerate(chunks, start=1):
       is_final = (seq_num == len(chunks))
       await _publish_response_chunk(command_id, payload, seq_num, is_final)
       if delay > 0:
           await asyncio.sleep(delay)
   # Update status to completed after all chunks
   await _update_command_status_completed(...)
   ```

#### **Tip 3: Existing Response Generators**

The current response generator functions (lines 27-135) generate COMPLETE responses:
- `_generate_read_dtc_response()` returns ALL DTCs in a single dict
- `_generate_clear_dtc_response()` returns a single status message
- `_generate_read_data_by_id_response()` returns a single data value

**You SHOULD create NEW generator functions** for streaming:
- `_generate_read_dtc_streaming_chunks()` → returns list of chunks
- `_generate_read_data_by_id_streaming_chunks()` → returns list of chunks
- Keep existing generators for backward compatibility in tests

#### **Tip 4: Redis Event Publishing**

The current implementation creates a new Redis client for EACH event (lines 231, 267, 342). This is acceptable but not optimal for multiple chunks.

**You COULD optimize** by:
- Creating a single Redis client at the start of `execute_command()`
- Reusing it for all chunk publications
- Closing it at the end
- **However:** This is NOT required for acceptance criteria - keep current pattern if time is limited

#### **Tip 5: Test Timing Verification**

For testing ~0.5 second delays, you SHOULD:
- Use `unittest.mock.patch("app.connectors.vehicle_connector.asyncio.sleep")` to mock sleep
- Verify sleep was called with correct delay values
- **DO NOT use `time.time()` to measure actual elapsed time** - this makes tests flaky and slow

Example from existing test (lines 141-144):
```python
mock_sleep.assert_called_once()
delay = mock_sleep.call_args[0][0]
assert 0.5 <= delay <= 1.5
```

For multi-chunk, adapt this to:
```python
assert mock_sleep.call_count == 2  # Two delays between 3 chunks
delays = [call[0][0] for call in mock_sleep.call_args_list]
assert all(d == pytest.approx(0.5, abs=0.1) for d in delays)
```

#### **Tip 6: Backward Compatibility**

The current `execute_command()` function is called by:
- Command service (triggers execution)
- Integration tests (test_websocket.py from I3.T1)

**You MUST ensure** that your changes do not break:
- The existing API signature
- The final command status update
- The audit logging behavior
- The error handling flow

#### **Warning: Sequence Number Correctness**

The database has a UNIQUE constraint on `(command_id, sequence_number)`. If you accidentally try to create two responses with the same sequence_number for the same command, you will get an `IntegrityError`.

**You MUST:**
- Start sequence_number at 1 (not 0)
- Increment by exactly 1 for each chunk
- Never skip sequence numbers (no gaps)

### Acceptance Criteria Breakdown

Let me map each acceptance criterion to implementation guidance:

✅ **"Command 'ReadDTC' generates 3 response chunks"**
   - Implement in `_generate_read_dtc_streaming_chunks()`
   - Return list of 3 payloads: [chunk1_dtc_p0420, chunk2_dtc_p0171, chunk3_final_status]

✅ **"Each chunk has incrementing sequence_number (1, 2, 3)"**
   - Use `enumerate(chunks, start=1)` in publish loop
   - Pass seq_num to `create_response()`

✅ **"Final chunk has is_final=true"**
   - Set `is_final = (seq_num == len(chunks))` in loop
   - Only last iteration will have is_final=True

✅ **"Chunks published with ~0.5 second intervals"**
   - Include delay value in chunk generation: `[(payload, 0.5), (payload, 0.5), (payload, 0)]`
   - Call `await asyncio.sleep(delay)` after publishing each non-final chunk

✅ **"WebSocket client receives all chunks in correct order"**
   - This is automatically handled by sequence_number ordering
   - WebSocket endpoint already implemented in I3.T1 - no changes needed

✅ **"Unit tests verify: correct number of chunks, sequence_number increments, timing delays"**
   - Write test `test_execute_command_read_dtc_streaming()`
   - Assert `create_response` called 3 times
   - Assert sequence_numbers are [1, 2, 3]
   - Assert is_final is [False, False, True]
   - Assert sleep called 2 times with ~0.5s delays

✅ **"Test coverage maintained ≥80%"**
   - Run `pytest --cov=app.connectors --cov-report=term` after implementation
   - Existing tests provide ~80% coverage - adding streaming tests should maintain this

✅ **"No linter errors"**
   - Run `ruff check backend/app/connectors/` before committing
   - Run `mypy backend/app/connectors/` to verify type hints
   - Ensure all functions have docstrings

### Recommended Implementation Steps

1. **Add streaming chunk generators** (new functions):
   - `_generate_read_dtc_streaming_chunks() -> list[tuple[dict, float]]`
   - `_generate_read_data_by_id_streaming_chunks(dataId) -> list[tuple[dict, float]]`

2. **Extract helper function** `_publish_response_chunk()`:
   - Takes: command_id, vehicle_id, payload, seq_num, is_final
   - Creates DB record
   - Publishes Redis event
   - Returns response object

3. **Refactor `execute_command()`**:
   - Replace single response generation with multi-chunk loop
   - Keep status update to "completed" at the end
   - Keep error handling as-is

4. **Add unit tests** in `test_vehicle_connector.py`:
   - `test_execute_command_read_dtc_streaming()`
   - `test_execute_command_read_data_by_id_streaming()`
   - `test_streaming_chunks_timing()`
   - `test_streaming_chunks_sequence_numbers()`
   - `test_streaming_final_chunk_flag()`

5. **Run tests and verify**:
   - Unit tests pass: `pytest backend/tests/unit/test_vehicle_connector.py -v`
   - Integration tests still pass: `pytest backend/tests/integration/test_websocket.py -v`
   - Coverage maintained: `pytest --cov=app.connectors --cov-report=term`

### Code Quality Standards

The existing code demonstrates high quality:
- Comprehensive docstrings with Args/Returns/Raises
- Type hints on all functions
- Structured logging with correlation IDs
- Proper error handling with try/except/finally
- Async/await best practices

**You MUST maintain the same quality standards** in your modifications:
- Add type hints: `list[tuple[dict[str, Any], float]]`
- Add docstrings to new functions
- Use structlog for all logging
- Handle errors gracefully
- Follow existing code formatting

### Final Notes

This task is a **refactoring and enhancement** rather than a complete rewrite. The existing code is production-ready and well-tested. Your changes should be **surgical and targeted** - modify only what's necessary to support multi-chunk streaming while preserving all existing behavior.

**Key Success Metrics:**
1. ReadDTC generates exactly 3 chunks
2. All existing tests still pass
3. New tests verify streaming behavior
4. WebSocket integration works end-to-end (test with I3.T1)
5. No regression in error handling or audit logging

**Estimated Effort:** 2-3 hours for implementation + 1-2 hours for comprehensive testing.

