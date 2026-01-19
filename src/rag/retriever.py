"""
RAG Retriever - 벡터 기반 혜택 검색
비용 최소화: sentence-transformers (무료, 로컬) + ChromaDB
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from .loader import BenefitLoader, BenefitDocument


class BenefitRetriever:
    """
    ChromaDB + sentence-transformers를 활용한 혜택 검색기
    
    비용 최소화:
    - sentence-transformers: 무료 로컬 임베딩
    - ChromaDB: 무료 로컬 벡터 DB
    """
    
    def __init__(
        self,
        collection_name: str = "benefits",
        persist_directory: str = None,
        embedding_model: str = "jhgan/ko-sbert-nli"  # 한국어 특화 모델
    ):
        self.collection_name = collection_name
        
        # 저장 경로 설정
        if persist_directory is None:
            base_dir = Path(__file__).parent.parent.parent
            persist_directory = str(base_dir / ".chroma_db")
        
        self.persist_directory = persist_directory
        self.embedding_model_name = embedding_model
        
        # 초기화
        self._init_embedding_model()
        self._init_chromadb()
        self._ensure_indexed()
    
    def _init_embedding_model(self):
        """임베딩 모델 초기화"""
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
        else:
            print("Warning: sentence-transformers not available, using fallback")
            self.embedding_model = None
    
    def _get_embedding(self, text: str) -> List[float]:
        """텍스트 임베딩 생성"""
        if self.embedding_model:
            return self.embedding_model.encode(text).tolist()
        else:
            # Fallback: 간단한 해시 기반 임베딩 (데모용)
            import hashlib
            hash_val = hashlib.md5(text.encode()).hexdigest()
            return [int(hash_val[i:i+2], 16) / 255.0 for i in range(0, 32, 2)]
    
    def _init_chromadb(self):
        """ChromaDB 초기화 (0.4+ 호환)"""
        if CHROMADB_AVAILABLE:
            try:
                # ChromaDB 0.4+ 방식 (PersistentClient)
                self.client = chromadb.PersistentClient(path=self.persist_directory)
            except (TypeError, AttributeError):
                # 구버전 fallback (0.3.x)
                self.client = chromadb.Client(Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=self.persist_directory,
                    anonymized_telemetry=False
                ))
            
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        else:
            print("Warning: ChromaDB not available, using in-memory fallback")
            self.client = None
            self.collection = None
            self._fallback_docs = []
    
    def _ensure_indexed(self):
        """혜택 데이터가 인덱싱되어 있는지 확인하고, 없으면 인덱싱"""
        if self.collection is not None:
            # ChromaDB 사용
            if self.collection.count() == 0:
                self._index_benefits()
        else:
            # Fallback: 메모리에 로드
            if not self._fallback_docs:
                loader = BenefitLoader()
                self._fallback_docs = loader.load()
    
    def _index_benefits(self):
        """혜택 데이터를 벡터 DB에 인덱싱"""
        loader = BenefitLoader()
        documents = loader.load()
        
        if not documents:
            print("No documents to index")
            return
        
        ids = []
        embeddings = []
        metadatas = []
        contents = []
        
        for doc in documents:
            ids.append(doc.metadata["id"])
            embeddings.append(self._get_embedding(doc.page_content))
            metadatas.append(doc.metadata)
            contents.append(doc.page_content)
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=contents
        )
        
        print(f"Indexed {len(documents)} benefit documents")
    
    def search(
        self,
        query: str,
        n_results: int = 3,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        쿼리와 유사한 혜택 검색
        
        Args:
            query: 검색 쿼리 (예: "청년 월세 지원", "전세 대출")
            n_results: 반환할 결과 수
            filters: 메타데이터 필터 (예: {"category": "주거비지원"})
        
        Returns:
            검색 결과 리스트
        """
        if self.collection is not None:
            # ChromaDB 검색
            query_embedding = self._get_embedding(query)
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filters
            )
            
            # 결과 포맷팅
            formatted = []
            for i, doc_id in enumerate(results["ids"][0]):
                formatted.append({
                    "id": doc_id,
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if results.get("distances") else None
                })
            
            return formatted
        else:
            # Fallback: 키워드 기반 검색
            return self._fallback_search(query, n_results)
    
    def _fallback_search(self, query: str, n_results: int) -> List[Dict]:
        """ChromaDB 없을 때 키워드 기반 검색"""
        results = []
        query_lower = query.lower()
        
        for doc in self._fallback_docs:
            score = 0
            content_lower = doc.page_content.lower()
            
            # 키워드 매칭 점수
            for word in query_lower.split():
                if word in content_lower:
                    score += 1
            
            if score > 0:
                results.append({
                    "id": doc.metadata["id"],
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score
                })
        
        # 점수순 정렬
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:n_results]
    
    def get_all_benefits(self) -> List[Dict[str, Any]]:
        """모든 혜택 데이터 반환"""
        if self.collection is not None:
            results = self.collection.get()
            formatted = []
            for i, doc_id in enumerate(results["ids"]):
                formatted.append({
                    "id": doc_id,
                    "content": results["documents"][i],
                    "metadata": results["metadatas"][i]
                })
            return formatted
        else:
            return [
                {"id": d.metadata["id"], "content": d.page_content, "metadata": d.metadata}
                for d in self._fallback_docs
            ]


if __name__ == "__main__":
    retriever = BenefitRetriever()
    
    # 테스트 검색
    print("=== 검색: '청년 월세 지원' ===")
    results = retriever.search("청년 월세 지원", n_results=2)
    for r in results:
        print(f"\n[{r['metadata']['name']}]")
        print(r['content'][:150] + "...")
    
    print("\n=== 검색: '전세 대출 저금리' ===")
    results = retriever.search("전세 대출 저금리", n_results=2)
    for r in results:
        print(f"\n[{r['metadata']['name']}]")
        print(r['content'][:150] + "...")
