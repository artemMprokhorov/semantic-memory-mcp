#!/bin/bash
# Recompute all embeddings with current model

echo "🔄 Recomputing embeddings..."

docker exec neural-memory-mcp python3 -c "
import sys
sys.path.insert(0, '/app/src')
from stable_embeddings import StableEmbeddingModel
import sqlite3

DB_PATH = '/app/data/memory.db'

print('Loading model...')
model = StableEmbeddingModel()

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute('SELECT id, content FROM notes')
notes = cursor.fetchall()

print(f'Recomputing {len(notes)} notes...')

for i, (note_id, content) in enumerate(notes):
    emb = model.encode([content])[0]
    cursor.execute('UPDATE notes SET embedding_vector = ? WHERE id = ?', 
                  (emb.tobytes(), note_id))
    if (i + 1) % 10 == 0:
        print(f'  {i+1}/{len(notes)}')

conn.commit()
conn.close()
print(f'✅ Done! Recomputed {len(notes)} embeddings')
"

echo ""
echo "Now recalibrating..."
docker exec neural-memory-mcp python3 /app/src/embedding_check.py --recalibrate

echo ""
echo "✅ Complete!"
