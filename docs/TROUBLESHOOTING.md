# Troubleshooting Guide

## Common Issues

### Search Returns 0 Results

**Symptom:** `Found 0 relevant notes (from 0 total matches)`

**Causes:**

1. **Empty database**
   - Check: `neural_stats` shows 0 notes
   - Fix: Add some notes first

2. **Embedding drift** (most common after rebuild)
   - Check logs for "MODEL DRIFT DETECTED"
   - Fix: Recompute embeddings

```bash
docker exec neural-memory-mcp python3 /app/scripts/recompute_embeddings.py
```

3. **Similarity threshold too high**
   - Default threshold: 0.4
   - Adjust in `mcp_sse_handler.py` if needed

### Embedding Drift Explained

**What is it?**

When you rebuild Docker image or update Python packages, the embedding model might produce slightly different vectors — even with the same weights.

**Why it happens:**
- Different library versions
- Floating point precision differences
- Model loading randomness

**Detection:**

On startup, server computes embeddings for test phrases and compares to saved calibration:

```
============================================================
🔍 EMBEDDING CONSISTENCY CHECK
============================================================
  Phrase 1: similarity = 0.847231    ← Should be ~1.0
  Phrase 2: similarity = 0.823156
  
❌ MODEL DRIFT DETECTED! min_sim=0.82 < 0.99
============================================================
```

**Fix:**

```bash
# Recompute all embeddings with current model
docker exec neural-memory-mcp python3 /app/scripts/recompute_embeddings.py

# Then recalibrate
docker exec neural-memory-mcp python3 /app/scripts/embedding_check.py --recalibrate
```

### Container Won't Start

**Check logs:**

```bash
docker logs neural-memory-mcp
```

**Common errors:**

1. **Port already in use**
```
Error: Port 5000 already in use
```
Fix: Change port in `docker-compose.yml` or stop conflicting service

2. **Out of memory**
```
Killed (OOM)
```
Fix: Ensure 4GB+ RAM available, close other apps

3. **Model download failed**
```
Connection error downloading model
```
Fix: Check internet, retry `docker-compose up --build`

### Claude Can't Connect

**Verify server is running:**

```bash
curl https://your-ngrok-url/health
```

Should return: `{"status": "ok"}`

**Test MCP endpoint:**

```bash
curl -X POST "https://your-ngrok-url/sse?api_key=YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

Should return tools list.

**Common issues:**

1. **ngrok not running** — Restart ngrok
2. **Wrong URL** — Check `/sse` suffix
3. **API key mismatch** — Verify key matches `.env`
4. **Firewall blocking** — Allow outbound HTTPS

### Slow Search Performance

**Normal performance:** < 500ms for 1000 notes

**If slow:**

1. **Too many notes** — Consider pruning old notes
2. **Large embeddings load** — First search after restart is slow
3. **CPU throttling** — Check system resources

**Optimization:**

Add FAISS index for 10K+ notes (see Architecture docs).

### Backup/Restore Issues

**Backup fails:**

```bash
# Check disk space
df -h

# Check permissions
ls -la /path/to/backup/dir
```

**Restore fails:**

```bash
# Verify backup integrity
ls -la /path/to/backup/
cat /path/to/backup/backup_info.json

# Manual restore
docker-compose down
cp -r /backup/data ./data
docker-compose up -d
```

### Database Corruption

**Symptoms:** Errors reading notes, inconsistent counts

**Fix:**

```bash
# Stop server
docker-compose down

# Check integrity
sqlite3 data/memory.db "PRAGMA integrity_check;"

# If corrupted, restore from backup
./scripts/restore.sh neural_memory_backup_YYYYMMDD
```

## Getting Help

1. **Check logs first:**
```bash
docker logs neural-memory-mcp --tail 100
```

2. **Enable debug mode:**
```bash
# In .env
FLASK_DEBUG=true
```

3. **Open issue on GitHub** with:
   - Error message
   - Steps to reproduce
   - Docker logs
   - System info (OS, RAM, Docker version)

## FAQ

**Q: Can I use a different embedding model?**

A: Yes, but you must recompute all embeddings after changing. Edit `stable_embeddings.py`.

**Q: How many notes can it handle?**

A: Tested with 10K notes, search < 1 second. For more, add FAISS indexing.

**Q: Is my data sent anywhere?**

A: No. Everything stays on your server. Only Claude.ai connects via your ngrok tunnel.

**Q: Can I use this without ngrok?**

A: Yes, if you have a public IP or reverse proxy. Server just needs to be HTTPS-accessible.
