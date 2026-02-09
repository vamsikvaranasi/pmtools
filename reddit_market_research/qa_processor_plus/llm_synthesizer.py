"""
OllamaLLMSynthesizer — LLM-based Synthesis for Mode C

Uses Ollama to generate cluster labels, "why it matters", and open questions.
"""

from typing import List, Dict, Any, Optional


class OllamaLLMSynthesizer:
    """Synthesizes insights using Ollama LLM."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the OllamaLLMSynthesizer.
        
        Args:
            config: Configuration with keys:
                - ollama_base_url: Ollama server URL
                - model: Model name
                - max_clusters_to_synthesize: Max clusters to process (cost control)
                - synthesis_temperature: Temperature for generation
        """
        self.base_url = config.get('ollama_base_url', 'http://localhost:11434')
        self.model = config.get('model', 'smollm2:360m')
        self.max_clusters = config.get('max_clusters_to_synthesize', 20)
        self.temperature = config.get('synthesis_temperature', 0.3)
    
    def generate_cluster_label(self, cluster_items: List[Dict[str, Any]]) -> Optional[str]:
        """
        Generate a concise label for a cluster of pain points.
        
        Args:
            cluster_items: List of items in the cluster
            
        Returns:
            Generated label or None
        """
        if not cluster_items:
            return None
        
        # Collect key information from cluster
        texts = [item.get('text', '')[:100] for item in cluster_items[:3]]
        prompt = f"""Generate a concise 3-5 word label for this cluster of related pain points:
{chr(10).join(texts)}

Label (just the label, no explanation):"""
        
        try:
            label = self._call_ollama(prompt)
            return label.strip() if label else None
        except Exception:
            return None
    
    def generate_why_it_matters(self, cluster_label: str, 
                               cluster_size: int, context: str = "") -> Optional[str]:
        """
        Generate business context for why this cluster matters.
        
        Args:
            cluster_label: Label for the cluster
            cluster_size: Number of items in cluster
            context: Additional context
            
        Returns:
            Generated explanation or None
        """
        prompt = f"""Why does this pain point matter for the business?
Pain point: {cluster_label}
Frequency: {cluster_size} mentions
Context: {context}

Explanation (1-2 sentences):"""
        
        try:
            text = self._call_ollama(prompt)
            return text.strip() if text else None
        except Exception:
            return None
    
    def generate_open_questions(self, cluster_label: str) -> List[str]:
        """
        Generate open questions that this pain point raises.
        
        Args:
            cluster_label: Label for the cluster
            
        Returns:
            List of generated questions
        """
        prompt = f"""What are 2-3 important questions to investigate about: {cluster_label}?

Questions (one per line):"""
        
        try:
            text = self._call_ollama(prompt)
            if not text:
                return []
            questions = [q.strip() for q in text.strip().split('\n') if q.strip()]
            return questions[:3]
        except Exception:
            return []
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        """
        Call Ollama API to generate text.
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            Generated text or None
        """
        try:
            import requests
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": self.temperature,
                    "stream": False
                },
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            return data.get('response', '').strip()
        except Exception as e:
            return None
