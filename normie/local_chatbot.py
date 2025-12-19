"""
Local AI Chatbot - Train on your own material
Uses RAG (Retrieval Augmented Generation) approach for personal use.

Requirements:
    pip install transformers torch sentence-transformers chromadb
"""

import os
import json
from pathlib import Path
from typing import List, Dict
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

class LocalChatbot:
    """
    Local chatbot that learns from your material using RAG.
    No external API calls - everything runs locally.
    """
    
    def __init__(self, material_folder: str = "material", model_name: str = "microsoft/DialoGPT-medium"):
        """
        Initialize the chatbot.
        
        Args:
            material_folder: Folder containing your training material (text files)
            model_name: HuggingFace model name (use smaller models for local training)
        """
        self.material_folder = Path(material_folder)
        self.material_folder.mkdir(exist_ok=True)
        
        # Initialize embedding model for RAG
        print("Loading embedding model...")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize language model (use smaller models for local use)
        print(f"Loading language model: {model_name}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        
        # Create vector database for RAG
        self.chroma_client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="./chroma_db"
        ))
        
        # Create or get collection
        try:
            self.collection = self.chroma_client.get_collection("knowledge_base")
        except:
            self.collection = self.chroma_client.create_collection("knowledge_base")
        
        # Load material into vector DB
        self._load_material()
        
        # Create text generation pipeline
        self.generator = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_length=512,
            temperature=0.7,
            do_sample=True
        )
    
    def _load_material(self):
        """Load all text files from material folder into vector database."""
        print("Loading material into knowledge base...")
        
        if not self.collection.count():
            # Load all text files
            text_files = list(self.material_folder.glob("*.txt"))
            text_files.extend(self.material_folder.glob("*.md"))
            
            if not text_files:
                print(f"No material files found in {self.material_folder}")
                print("Create .txt or .md files with your content!")
                return
            
            documents = []
            metadatas = []
            ids = []
            
            for idx, file_path in enumerate(text_files):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Split into chunks (for better retrieval)
                    chunks = self._chunk_text(content, chunk_size=500)
                    
                    for chunk_idx, chunk in enumerate(chunks):
                        documents.append(chunk)
                        metadatas.append({"source": str(file_path), "chunk": chunk_idx})
                        ids.append(f"{file_path.stem}_{chunk_idx}")
            
            if documents:
                # Generate embeddings and store
                embeddings = self.embedder.encode(documents).tolist()
                self.collection.add(
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                print(f"Loaded {len(documents)} chunks from {len(text_files)} files")
    
    def _chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Split text into chunks for better retrieval."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            current_chunk.append(word)
            current_length += len(word) + 1
            
            if current_length >= chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_length = 0
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def _retrieve_relevant_context(self, query: str, top_k: int = 3) -> str:
        """Retrieve relevant context from knowledge base using RAG."""
        # Generate query embedding
        query_embedding = self.embedder.encode([query]).tolist()[0]
        
        # Search in vector DB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        if results['documents'] and results['documents'][0]:
            # Combine retrieved documents
            context = "\n".join(results['documents'][0])
            return context
        
        return ""
    
    def chat(self, user_input: str) -> str:
        """
        Chat with the bot using RAG.
        
        Args:
            user_input: User's question/message
            
        Returns:
            Bot's response
        """
        # Retrieve relevant context
        context = self._retrieve_relevant_context(user_input)
        
        # Build prompt with context
        if context:
            prompt = f"""Based on the following knowledge:
{context}

User: {user_input}
Assistant:"""
        else:
            prompt = f"User: {user_input}\nAssistant:"
        
        # Generate response
        response = self.generator(
            prompt,
            max_new_tokens=150,
            temperature=0.7,
            do_sample=True,
            pad_token_id=self.tokenizer.eos_token_id
        )
        
        # Extract generated text
        generated_text = response[0]['generated_text']
        
        # Extract only the assistant's response
        if "Assistant:" in generated_text:
            assistant_response = generated_text.split("Assistant:")[-1].strip()
        else:
            assistant_response = generated_text[len(prompt):].strip()
        
        return assistant_response
    
    def add_material(self, text: str, source_name: str = "manual_input"):
        """Add new material to the knowledge base."""
        chunks = self._chunk_text(text)
        embeddings = self.embedder.encode(chunks).tolist()
        
        documents = chunks
        metadatas = [{"source": source_name, "chunk": i} for i in range(len(chunks))]
        ids = [f"{source_name}_{i}" for i in range(len(chunks))]
        
        self.collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Added {len(chunks)} chunks to knowledge base")


def main():
    """Example usage."""
    print("=" * 60)
    print("Local AI Chatbot - Personal Use Only")
    print("=" * 60)
    
    # Initialize chatbot
    chatbot = LocalChatbot(material_folder="material")
    
    print("\nChatbot ready! Type 'quit' to exit.\n")
    
    # Interactive chat loop
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if not user_input:
            continue
        
        print("Bot: ", end="", flush=True)
        response = chatbot.chat(user_input)
        print(response)
        print()


if __name__ == "__main__":
    main()

