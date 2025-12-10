# Logging System

The application now uses structured file-based logging for better tracking and debugging.

## Log Files Location

All logs are stored in the `logs/` directory:

```
backend/
├── logs/
│   ├── app.log              # General application logs
│   ├── categorization.log   # AI categorization specific logs
│   └── errors.log           # Errors and exceptions only
```

## Log Files Description

### `app.log`
- **Purpose**: General application logs
- **Level**: INFO and above
- **Contains**: All application events, startup, requests, background tasks
- **Rotation**: 10MB per file, keeps 5 backups

### `categorization.log`
- **Purpose**: AI categorization tracking
- **Level**: INFO and above
- **Contains**:
  - CSV upload events
  - Background categorization progress
  - Batch processing status
  - Retry attempts
  - Success/failure details
- **Rotation**: 10MB per file, keeps 5 backups

### `errors.log`
- **Purpose**: Errors and exceptions only
- **Level**: ERROR and above
- **Contains**: All application errors with full stack traces
- **Rotation**: 10MB per file, keeps 5 backups

## Log Format

```
2025-12-02 21:30:45 | INFO     | categorization | 📦 Processing batch 1/5 (10 transactions)...
2025-12-02 21:30:48 | INFO     | categorization |    ✅ Batch 1 complete: 10/10 successful
2025-12-02 21:30:49 | WARNING  | categorization |    ⚠️  2 failed, retrying 2 transactions (attempt 1/2)...
2025-12-02 21:30:51 | ERROR    | categorization |    ❌ Max retries reached. 2 transactions still failed.
```

## Viewing Logs

### Real-time monitoring (Linux/Mac):
```bash
# Watch categorization progress
tail -f logs/categorization.log

# Watch all application events
tail -f logs/app.log

# Watch errors only
tail -f logs/errors.log
```

### Real-time monitoring (Windows PowerShell):
```powershell
# Watch categorization progress
Get-Content logs\categorization.log -Wait -Tail 50

# Watch all application events
Get-Content logs\app.log -Wait -Tail 50

# Watch errors only
Get-Content logs\errors.log -Wait -Tail 50
```

### Search logs:
```bash
# Find all failed categorizations
grep "failed" logs/categorization.log

# Find specific transaction
grep "transaction 42" logs/categorization.log

# Find errors in the last hour
grep "2025-12-02 21:" logs/errors.log
```

## Log Rotation

- Log files automatically rotate when they reach 10MB
- Up to 5 backup files are kept (e.g., `app.log.1`, `app.log.2`, etc.)
- Oldest backups are automatically deleted
- No manual cleanup needed

## Categorization Log Example

```
================================================================================
2025-12-02 21:25:15 | INFO     | categorization | 🤖 Starting background categorization for 50 transactions
2025-12-02 21:25:15 | INFO     | categorization |    Batch size: 10
2025-12-02 21:25:15 | INFO     | categorization |    Total batches: 5
2025-12-02 21:25:15 | INFO     | categorization |    Max retries: 2
================================================================================
2025-12-02 21:25:15 | INFO     | categorization | 📦 Processing batch 1/5 (10 transactions)...
2025-12-02 21:25:18 | INFO     | categorization |    ✅ Batch 1 complete: 10/10 successful
2025-12-02 21:25:19 | INFO     | categorization | 📦 Processing batch 2/5 (10 transactions)...
2025-12-02 21:25:22 | INFO     | categorization |    ✅ Batch 2 complete: 8/10 successful
2025-12-02 21:25:22 | WARNING  | categorization |    ⚠️  2 failed, retrying 2 transactions (attempt 1/2)...
2025-12-02 21:25:24 | INFO     | categorization |    🔄 Retry 1 complete: 2/2 successful
2025-12-02 21:25:25 | INFO     | categorization | 📦 Processing batch 3/5 (10 transactions)...
2025-12-02 21:25:28 | INFO     | categorization |    ✅ Batch 3 complete: 10/10 successful
2025-12-02 21:25:29 | INFO     | categorization | 📦 Processing batch 4/5 (10 transactions)...
2025-12-02 21:25:32 | INFO     | categorization |    ✅ Batch 4 complete: 10/10 successful
2025-12-02 21:25:33 | INFO     | categorization | 📦 Processing batch 5/5 (10 transactions)...
2025-12-02 21:25:36 | INFO     | categorization |    ✅ Batch 5 complete: 10/10 successful
================================================================================
2025-12-02 21:25:36 | INFO     | categorization | ✅ Background categorization complete!
================================================================================
```

## Configuration

Logging is configured in `app/core/logging_config.py`. You can modify:
- Log levels
- File sizes
- Number of backups
- Log formats
- Add new log files

## Tips

1. **Monitor progress**: Use `tail -f logs/categorization.log` to watch real-time categorization
2. **Debug issues**: Check `errors.log` first for any exceptions
3. **Track specific events**: Search logs by transaction ID or merchant name
4. **Archive logs**: Log files are automatically rotated, but you can archive them manually if needed
5. **Console output**: Logs also appear in console, but file logs are more permanent and searchable
