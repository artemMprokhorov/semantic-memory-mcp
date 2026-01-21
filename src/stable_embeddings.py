#!/usr/bin/env python3
"""
Stable Embeddings using HuggingFace Transformers
Direct implementation avoids sentence-transformers ARM64 issues
"""

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel
from typing import List, Union
import os


class StableEmbeddingModel:
    """Direct transformers implementation for stable embeddings"""
    
    def __init__(self, model_name: str = None):
        """
        Initialize embedding model
        
        Args:
            model_name: HuggingFace model name (default: all-MiniLM-L6-v2)
        """
        model_name = model_name or os.getenv(
            'EMBEDDING_MODEL', 
            'sentence-transformers/all-MiniLM-L6-v2'
        )
        
        print(f"🤖 Loading model: {model_name}")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            self.model.eval()
            
            # CPU only for stability
            self.device = torch.device('cpu')
            self.model.to(self.device)
            
            print(f"✅ Model loaded on {self.device}")
            
        except Exception as e:
            print(f"❌ Model loading failed: {e}")
            raise
    
    def encode(self, sentences: Union[str, List[str]]) -> np.ndarray:
        """
        Encode sentences to embeddings
        
        Args:
            sentences: Single string or list of strings
            
        Returns:
            numpy array of shape (n_sentences, embedding_dim)
        """
        # Handle single string
        if isinstance(sentences, str):
            sentences = [sentences]
        
        try:
            # Tokenize
            inputs = self.tokenizer(
                sentences,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors='pt'
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Forward pass
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # Mean pooling
            embeddings = self._mean_pooling(
                outputs.last_hidden_state, 
                inputs['attention_mask']
            )
            
            return embeddings.cpu().numpy()
            
        except Exception as e:
            print(f"❌ Encoding failed: {e}")
            raise
    
    def _mean_pooling(self, embeddings: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        """Mean pooling with attention mask"""
        mask_expanded = attention_mask.unsqueeze(-1).expand(embeddings.size()).float()
        sum_embeddings = torch.sum(embeddings * mask_expanded, dim=1)
        sum_mask = torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
        return sum_embeddings / sum_mask


def test_embeddings():
    """Test embedding functionality"""
    print("🧪 Testing embeddings...")
    
    model = StableEmbeddingModel()
    
    sentences = [
        "Machine learning is fascinating.",
        "Deep learning uses neural networks.",
        "I like pizza and pasta."
    ]
    
    embeddings = model.encode(sentences)
    print(f"Shape: {embeddings.shape}")
    
    # Test similarity
    def cosine_sim(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    sim_related = cosine_sim(embeddings[0], embeddings[1])
    sim_unrelated = cosine_sim(embeddings[0], embeddings[2])
    
    print(f"ML vs DL similarity: {sim_related:.4f}")
    print(f"ML vs Food similarity: {sim_unrelated:.4f}")
    
    assert sim_related > sim_unrelated, "Semantic similarity check failed"
    print("✅ Test passed!")


if __name__ == "__main__":
    test_embeddings()
