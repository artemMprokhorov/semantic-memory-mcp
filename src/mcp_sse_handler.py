#!/usr/bin/env python3
"""
MCP SSE Handler for Neural Memory
Implements Model Context Protocol with Server-Sent Events transport
"""

from flask import Flask, Response, request, stream_with_context, jsonify
import json
import sqlite3
import numpy as np
import hashlib
import hmac
import os
from datetime import datetime

# Configuration
DB_PATH = os.getenv('DB_PATH', '/app/data/memory.db')
API_KEY = os.getenv('NEURAL_API_KEY', 'change_me_in_production')
API_KEY_HASH = hashlib.sha256(API_KEY.encode()).hexdigest()

# Lazy-loaded embedding model
embedding_model = None


def get_model():
    """Lazy load embedding model"""
    global embedding_model
    if embedding_model is None:
        from stable_embeddings import StableEmbeddingModel
        embedding_model = StableEmbeddingModel()
    return embedding_model


def verify_auth(request):
    """Verify API key from URL parameter or Authorization header"""
    # Check URL parameter
    url_key = request.args.get('api_key')
    if url_key:
        key_hash = hashlib.sha256(url_key.encode()).hexdigest()
        return hmac.compare_digest(key_hash, API_KEY_HASH)
    
    # Check Authorization header
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header[7:]
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return hmac.compare_digest(token_hash, API_KEY_HASH)
    
    return False


def handle_mcp_request(method, params):
    """Route MCP requests to appropriate handlers"""
    try:
        if method == 'initialize':
            return {
                'protocolVersion': '2024-11-05',
                'capabilities': {'tools': {}},
                'serverInfo': {
                    'name': 'neural-memory',
                    'version': '1.0.0'
                }
            }
        
        elif method == 'tools/list':
            return {
                'tools': [
                    {
                        'name': 'search_neural_memory',
                        'description': 'Search through notes using semantic similarity',
                        'inputSchema': {
                            'type': 'object',
                            'properties': {
                                'query': {'type': 'string', 'description': 'Search query'},
                                'limit': {'type': 'integer', 'default': 5, 'minimum': 1, 'maximum': 20}
                            },
                            'required': ['query']
                        }
                    },
                    {
                        'name': 'neural_stats',
                        'description': 'Get statistics about stored notes',
                        'inputSchema': {'type': 'object', 'properties': {}}
                    },
                    {
                        'name': 'add_note',
                        'description': 'Add new note with automatic embedding',
                        'inputSchema': {
                            'type': 'object',
                            'properties': {
                                'content': {'type': 'string', 'description': 'Note content'},
                                'category': {'type': 'string', 'default': 'general'}
                            },
                            'required': ['content']
                        }
                    },
                    {
                        'name': 'update_note',
                        'description': 'Update existing note by ID',
                        'inputSchema': {
                            'type': 'object',
                            'properties': {
                                'note_id': {'type': 'integer'},
                                'content': {'type': 'string'},
                                'category': {'type': 'string'}
                            },
                            'required': ['note_id', 'content']
                        }
                    },
                    {
                        'name': 'delete_note',
                        'description': 'Delete note by ID',
                        'inputSchema': {
                            'type': 'object',
                            'properties': {
                                'note_id': {'type': 'integer'}
                            },
                            'required': ['note_id']
                        }
                    }
                ]
            }
        
        elif method == 'tools/call':
            return handle_tool_call(params)
        
        return {'error': {'code': -32601, 'message': f'Method not found: {method}'}}
    
    except Exception as e:
        return {'error': {'code': -32603, 'message': str(e)}}


def handle_tool_call(params):
    """Execute tool calls"""
    tool_name = params.get('name')
    args = params.get('arguments', {})
    
    if tool_name == 'search_neural_memory':
        return search_notes(args.get('query', ''), args.get('limit', 5))
    
    elif tool_name == 'neural_stats':
        return get_stats()
    
    elif tool_name == 'add_note':
        return add_note(args.get('content', ''), args.get('category', 'general'))
    
    elif tool_name == 'update_note':
        return update_note(args.get('note_id'), args.get('content'), args.get('category'))
    
    elif tool_name == 'delete_note':
        return delete_note(args.get('note_id'))
    
    return {'error': {'code': -32602, 'message': f'Unknown tool: {tool_name}'}}


def search_notes(query, limit):
    """Semantic search through notes"""
    model = get_model()
    query_emb = model.encode([query])[0]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, content, category, timestamp, embedding_vector FROM notes WHERE embedding_vector IS NOT NULL')
    
    results = []
    for row in cursor.fetchall():
        note_id, content, category, timestamp, emb_blob = row
        note_emb = np.frombuffer(emb_blob, dtype=np.float32)
        
        # Cosine similarity
        sim = float(np.dot(query_emb, note_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(note_emb)))
        
        if sim >= 0.4:  # Threshold
            results.append({
                'id': note_id,
                'content': content,
                'category': category,
                'similarity': round(sim, 4)
            })
    
    conn.close()
    results.sort(key=lambda x: x['similarity'], reverse=True)
    top_results = results[:limit]
    
    text = f'Found {len(top_results)} relevant notes (from {len(results)} total matches):\n\n'
    for r in top_results:
        text += f'[ID:{r["id"]}] [{r["category"]}] (similarity: {r["similarity"]})\n{r["content"]}\n\n'
    
    return {'content': [{'type': 'text', 'text': text}]}


def get_stats():
    """Get memory statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM notes')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT category, COUNT(*) FROM notes GROUP BY category')
    by_category = {row[0]: row[1] for row in cursor.fetchall()}
    
    conn.close()
    
    text = f'Neural Memory Statistics:\n\nTotal notes: {total}\n\nBy category:\n'
    for cat, count in sorted(by_category.items()):
        text += f'  - {cat}: {count}\n'
    
    return {'content': [{'type': 'text', 'text': text}]}


def add_note(content, category):
    """Add new note with embedding"""
    if not content:
        return {'error': {'code': -32602, 'message': 'Content required'}}
    
    model = get_model()
    embedding = model.encode([content])[0]
    timestamp = datetime.now().isoformat()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO notes (content, category, timestamp, embedding_vector) VALUES (?, ?, ?, ?)',
        (content, category, timestamp, embedding.tobytes())
    )
    note_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    text = f'✅ Added note #{note_id}\nCategory: {category}\nContent: {content}'
    return {'content': [{'type': 'text', 'text': text}]}


def update_note(note_id, content, category=None):
    """Update existing note"""
    if not note_id or not content:
        return {'error': {'code': -32602, 'message': 'Note ID and content required'}}
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT category FROM notes WHERE id = ?', (note_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return {'error': {'code': -32602, 'message': f'Note #{note_id} not found'}}
    
    model = get_model()
    embedding = model.encode([content])[0]
    timestamp = datetime.now().isoformat()
    final_category = category or existing[0]
    
    cursor.execute(
        'UPDATE notes SET content=?, category=?, timestamp=?, embedding_vector=? WHERE id=?',
        (content, final_category, timestamp, embedding.tobytes(), note_id)
    )
    conn.commit()
    conn.close()
    
    text = f'✅ Updated note #{note_id}\nCategory: {final_category}\nContent: {content}'
    return {'content': [{'type': 'text', 'text': text}]}


def delete_note(note_id):
    """Delete note"""
    if not note_id:
        return {'error': {'code': -32602, 'message': 'Note ID required'}}
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT content, category FROM notes WHERE id = ?', (note_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return {'error': {'code': -32602, 'message': f'Note #{note_id} not found'}}
    
    cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    conn.commit()
    conn.close()
    
    text = f'✅ Deleted note #{note_id}\nWas: [{existing[1]}] {existing[0][:100]}...'
    return {'content': [{'type': 'text', 'text': text}]}


def create_mcp_endpoint(app):
    """Register MCP SSE endpoint with Flask app"""
    
    @app.route('/sse', methods=['POST', 'GET'])
    def mcp_sse():
        if not verify_auth(request):
            return jsonify({'error': 'Unauthorized'}), 401
        
        def generate():
            try:
                data = request.get_json() if request.method == 'POST' else {}
                method = data.get('method', 'initialize')
                params = data.get('params', {})
                req_id = data.get('id', 1)
                
                result = handle_mcp_request(method, params)
                response = {'jsonrpc': '2.0', 'id': req_id, 'result': result}
                yield f'data: {json.dumps(response)}\n\n'
            
            except Exception as e:
                error = {'jsonrpc': '2.0', 'id': 1, 'error': {'code': -32603, 'message': str(e)}}
                yield f'data: {json.dumps(error)}\n\n'
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Access-Control-Allow-Origin': '*'
            }
        )
    
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'ok'})
