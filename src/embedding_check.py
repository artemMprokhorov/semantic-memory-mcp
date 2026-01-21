#!/usr/bin/env python3
"""
Embedding Consistency Check
Detects model drift that breaks semantic search
"""

import sys
import os
import json
import numpy as np
from pathlib import Path

CALIBRATION_FILE = os.getenv('CALIBRATION_FILE', '/app/data/embedding_calibration.json')
SIMILARITY_THRESHOLD = 0.99

CALIBRATION_PHRASES = [
    "The quick brown fox jumps over the lazy dog.",
    "Semantic search uses vector embeddings.",
    "Python programming and machine learning."
]


def load_calibration():
    """Load saved calibration data"""
    if os.path.exists(CALIBRATION_FILE):
        with open(CALIBRATION_FILE, 'r') as f:
            return json.load(f)
    return None


def save_calibration(data):
    """Save calibration data"""
    os.makedirs(os.path.dirname(CALIBRATION_FILE), exist_ok=True)
    with open(CALIBRATION_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print(f'✅ Calibration saved to {CALIBRATION_FILE}')


def cosine_similarity(a, b):
    """Compute cosine similarity"""
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def compute_calibration(model):
    """Compute embeddings for calibration phrases"""
    embeddings = model.encode(CALIBRATION_PHRASES)
    return {
        'phrases': CALIBRATION_PHRASES,
        'embeddings': [emb.tolist() for emb in embeddings]
    }


def check_consistency(model):
    """
    Check if model produces consistent embeddings
    
    Returns:
        (is_consistent: bool, message: str)
    """
    saved = load_calibration()
    
    if saved is None:
        print('⚠️  No calibration found. Creating initial calibration...')
        calibration = compute_calibration(model)
        save_calibration(calibration)
        return True, 'Initial calibration created'
    
    # Compute current embeddings
    current = model.encode(CALIBRATION_PHRASES)
    
    # Compare
    similarities = []
    for i, (curr, saved_emb) in enumerate(zip(current, saved['embeddings'])):
        sim = cosine_similarity(curr, saved_emb)
        similarities.append(sim)
        print(f'  Phrase {i+1}: similarity = {sim:.6f}')
    
    min_sim = min(similarities)
    avg_sim = np.mean(similarities)
    
    print(f'\n  Average: {avg_sim:.6f}')
    print(f'  Minimum: {min_sim:.6f}')
    print(f'  Threshold: {SIMILARITY_THRESHOLD}')
    
    if min_sim >= SIMILARITY_THRESHOLD:
        return True, f'Model consistent (min_sim={min_sim:.4f})'
    else:
        return False, f'MODEL DRIFT DETECTED! min_sim={min_sim:.4f} < {SIMILARITY_THRESHOLD}'


def run_check():
    """Run consistency check"""
    print('=' * 60)
    print('🔍 EMBEDDING CONSISTENCY CHECK')
    print('=' * 60)
    
    try:
        # Import here to allow module to be imported without model
        sys.path.insert(0, os.path.dirname(__file__))
        from stable_embeddings import StableEmbeddingModel
        
        model = StableEmbeddingModel()
        is_ok, message = check_consistency(model)
        
        if is_ok:
            print(f'\n✅ {message}')
        else:
            print(f'\n❌ {message}')
            print('\n⚠️  Search results may be inaccurate!')
            print('   Fix: python3 scripts/recompute_embeddings.py')
        
        print('=' * 60)
        return 0 if is_ok else 1
        
    except Exception as e:
        print(f'\n❌ Check failed: {e}')
        return 1


def recalibrate():
    """Force recalibration"""
    print('🔄 Recalibrating...')
    
    sys.path.insert(0, os.path.dirname(__file__))
    from stable_embeddings import StableEmbeddingModel
    
    model = StableEmbeddingModel()
    calibration = compute_calibration(model)
    save_calibration(calibration)
    print('✅ Recalibration complete')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--recalibrate':
        recalibrate()
    else:
        sys.exit(run_check())
