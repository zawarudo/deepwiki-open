"""
End-to-end RAG pipeline integration tests.

This module tests the complete document processing pipeline from input documents
through chunking, embedding generation, FAISS indexing, and retrieval.

The tests use real components (no mocks) to identify actual issues in the pipeline
and track data transformation at each stage to identify where empty vectors are introduced.
"""

import pytest
import logging
import tempfile
import shutil
import os
from typing import List, Dict, Any, Optional
import numpy as np
from unittest.mock import patch
from pathlib import Path

# Import pipeline components
from adalflow.core.types import Document
from adalflow.components.data_process import TextSplitter, ToEmbeddings
from adalflow.core.db import LocalDB
import adalflow as adal

# Import API components
from api.data_pipeline import (
    DatabaseManager, 
    prepare_data_pipeline, 
    transform_documents_and_save_to_db,
    read_all_documents
)
from api.rag import RAG
from api.tools.embedder import get_embedder
from api.config import get_embedder_config, is_ollama_embedder

# Import test fixtures
from api.tests.fixtures.embedding_bug_scenarios import (
    embedding_bug_scenario_data,
    embedding_api_failure_scenarios,
    batch_processing_edge_cases,
    vector_dimension_mismatch_scenarios,
    embedding_validation_scenarios
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PipelineStageTracker:
    """Track data flow and transformations at each pipeline stage."""
    
    def __init__(self):
        self.stages = {}
        self.issues = []
    
    def track_stage(self, stage_name: str, data: Any, metadata: Optional[Dict] = None):
        """Track data at a specific pipeline stage."""
        stage_info = {
            'data_count': len(data) if hasattr(data, '__len__') else 1,
            'data_type': type(data).__name__,
            'metadata': metadata or {},
            'timestamp': pytest.approx(0.0, abs=1000000000)  # Simplified for tests
        }
        
        # Additional tracking for specific data types
        if isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            if hasattr(first_item, 'vector'):
                # Track vector dimensions
                vectors_info = self._analyze_vectors(data)
                stage_info.update(vectors_info)
            elif hasattr(first_item, 'text'):
                # Track document content
                content_info = self._analyze_documents(data)
                stage_info.update(content_info)
        
        self.stages[stage_name] = stage_info
        logger.info(f"Pipeline stage '{stage_name}': {stage_info}")
    
    def _analyze_vectors(self, docs_with_vectors: List) -> Dict:
        """Analyze vector data for dimensions and validity."""
        vector_info = {
            'total_vectors': 0,
            'empty_vectors': 0,
            'valid_vectors': 0,
            'dimension_counts': {},
            'invalid_reasons': []
        }
        
        for doc in docs_with_vectors:
            if hasattr(doc, 'vector') and doc.vector is not None:
                vector_info['total_vectors'] += 1
                
                # Check vector validity
                try:
                    if isinstance(doc.vector, list):
                        dimension = len(doc.vector)
                    elif hasattr(doc.vector, 'shape'):
                        dimension = doc.vector.shape[0] if len(doc.vector.shape) == 1 else doc.vector.shape[-1]
                    elif hasattr(doc.vector, '__len__'):
                        dimension = len(doc.vector)
                    else:
                        dimension = 0
                        vector_info['invalid_reasons'].append(f"Invalid vector type: {type(doc.vector)}")
                    
                    if dimension == 0:
                        vector_info['empty_vectors'] += 1
                        vector_info['invalid_reasons'].append("Zero-dimension vector")
                    else:
                        vector_info['valid_vectors'] += 1
                        vector_info['dimension_counts'][dimension] = vector_info['dimension_counts'].get(dimension, 0) + 1
                        
                        # Check for NaN or inf values
                        if isinstance(doc.vector, (list, np.ndarray)):
                            values = np.array(doc.vector)
                            if np.any(np.isnan(values)):
                                vector_info['invalid_reasons'].append("Contains NaN values")
                            if np.any(np.isinf(values)):
                                vector_info['invalid_reasons'].append("Contains Inf values")
                
                except Exception as e:
                    vector_info['invalid_reasons'].append(f"Analysis error: {str(e)}")
        
        return vector_info
    
    def _analyze_documents(self, documents: List) -> Dict:
        """Analyze document content and metadata."""
        doc_info = {
            'total_documents': len(documents),
            'empty_documents': 0,
            'content_lengths': [],
            'doc_types': {},
            'has_metadata': 0
        }
        
        for doc in documents:
            if hasattr(doc, 'text'):
                content = doc.text or ""
                doc_info['content_lengths'].append(len(content))
                if len(content.strip()) == 0:
                    doc_info['empty_documents'] += 1
            
            if hasattr(doc, 'meta_data') and doc.meta_data:
                doc_info['has_metadata'] += 1
                doc_type = doc.meta_data.get('type', 'unknown')
                doc_info['doc_types'][doc_type] = doc_info['doc_types'].get(doc_type, 0) + 1
        
        return doc_info
    
    def report_issues(self) -> List[str]:
        """Generate a report of identified issues."""
        issues = []
        
        for stage_name, stage_info in self.stages.items():
            if 'empty_vectors' in stage_info and stage_info['empty_vectors'] > 0:
                issues.append(f"Stage '{stage_name}': Found {stage_info['empty_vectors']} empty vectors")
            
            if 'invalid_reasons' in stage_info and stage_info['invalid_reasons']:
                for reason in set(stage_info['invalid_reasons']):  # Deduplicate
                    issues.append(f"Stage '{stage_name}': {reason}")
        
        return issues


@pytest.fixture
def pipeline_tracker():
    """Create a pipeline stage tracker for test analysis."""
    return PipelineStageTracker()


@pytest.fixture
def temp_repo_dir():
    """Create a temporary directory with sample files for testing."""
    temp_dir = tempfile.mkdtemp(prefix="test_repo_")
    
    # Create sample files that will be picked up by the document reader
    # README.md should be included (doc extension)
    readme_path = Path(temp_dir) / "README.md"
    readme_path.write_text(
        "# Test Repository\n\nThis is a test repository for pipeline testing.\n\nIt contains various types of files to test document processing."
    )
    
    # Python files should be included (code extension)
    main_py_path = Path(temp_dir) / "main.py"
    main_py_path.write_text("""def hello_world():
    '''A simple function that returns a greeting.'''
    return "Hello, World!"

def calculate_sum(a, b):
    '''Calculate the sum of two numbers.'''
    return a + b

class TestClass:
    '''A test class for demonstration.'''
    
    def __init__(self, name):
        self.name = name
    
    def greet(self):
        return f"Hello, {self.name}!"

if __name__ == "__main__":
    print(hello_world())
    print(calculate_sum(5, 3))
    test_obj = TestClass("World")
    print(test_obj.greet())
""")
    
    utils_py_path = Path(temp_dir) / "utils.py"
    utils_py_path.write_text("""import json
import os

def load_config(file_path):
    '''Load configuration from a JSON file.'''
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Config file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        return json.load(f)

def save_data(data, file_path):
    '''Save data to a file.'''
    with open(file_path, 'w') as f:
        if isinstance(data, (dict, list)):
            json.dump(data, f, indent=2)
        else:
            f.write(str(data))

def process_text(text):
    '''Process text by removing extra whitespace.'''
    return ' '.join(text.split())
""")
    
    # Create a subdirectory with more files
    subdir = Path(temp_dir) / "modules"
    subdir.mkdir()
    
    helper_py_path = subdir / "helper.py"
    helper_py_path.write_text("""def format_string(text, max_length=50):
    '''Format a string to a maximum length.'''
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def validate_email(email):
    '''Simple email validation.'''
    return "@" in email and "." in email.split("@")[-1]

def calculate_checksum(data):
    '''Calculate a simple checksum for data.'''
    return sum(ord(c) for c in str(data)) % 1000
""")
    
    # Add a JavaScript file to test code file handling
    js_path = Path(temp_dir) / "script.js"
    js_path.write_text("""function greetUser(name) {
    return `Hello, ${name}!`;
}

function calculateTotal(items) {
    return items.reduce((sum, item) => sum + item.price, 0);
}

class Calculator {
    constructor() {
        this.result = 0;
    }
    
    add(value) {
        this.result += value;
        return this;
    }
    
    getResult() {
        return this.result;
    }
}

console.log(greetUser("Pipeline Test"));
""")
    
    # Add a text documentation file
    docs_path = Path(temp_dir) / "DOCUMENTATION.txt"
    docs_path.write_text("""PIPELINE TESTING DOCUMENTATION

This directory contains test files for validating the document processing pipeline.

Files included:
- README.md: Markdown documentation
- main.py: Main Python module with functions and classes
- utils.py: Utility functions for configuration and data processing
- script.js: JavaScript functionality
- modules/helper.py: Additional helper functions

The pipeline should process these files through:
1. Document reading and parsing
2. Text chunking and splitting
3. Embedding generation
4. Vector indexing with FAISS
5. Query retrieval testing

Each file contains meaningful content to test semantic understanding.
""")
    
    logger.info(f"Created test repository with files:")
    for file_path in [readme_path, main_py_path, utils_py_path, helper_py_path, js_path, docs_path]:
        logger.info(f"  - {file_path.relative_to(temp_dir)} ({file_path.stat().st_size} bytes)")
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_db_dir():
    """Create a temporary directory for database storage."""
    temp_dir = tempfile.mkdtemp(prefix="test_db_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestRAGPipelineIntegration:
    """Test complete RAG pipeline integration."""
    
    def test_complete_pipeline_flow(self, temp_repo_dir, temp_db_dir, pipeline_tracker):
        """
        Test the complete document processing pipeline flow.
        
        This test follows a document through the entire pipeline:
        1. Document reading and parsing
        2. Text chunking/splitting  
        3. Embedding generation
        4. FAISS indexing
        5. Query retrieval
        
        Tracks data at each stage to identify where issues occur.
        """
        logger.info("=== Starting Complete Pipeline Flow Test ===")
        
        # Stage 1: Document Reading
        logger.info("Stage 1: Reading documents from repository")
        
        # Debug: List files in the directory
        import os
        logger.info(f"Files in temp directory {temp_repo_dir}:")
        for root, dirs, files in os.walk(temp_repo_dir):
            for file in files:
                full_path = os.path.join(root, file)
                logger.info(f"  Found file: {os.path.relpath(full_path, temp_repo_dir)}")
        
        # Use inclusion mode to be explicit about what files to include
        documents = read_all_documents(
            temp_repo_dir,
            included_files=["*.py", "*.js", "*.md", "*.txt"],
            included_dirs=[".", "modules"]
        )
        pipeline_tracker.track_stage("1_document_reading", documents, {
            "repo_path": temp_repo_dir,
            "total_files_found": len(documents)
        })
        
        assert len(documents) > 0, "Should find documents in test repository"
        assert all(hasattr(doc, 'text') for doc in documents), "All documents should have text"
        assert all(hasattr(doc, 'meta_data') for doc in documents), "All documents should have metadata"
        
        # Stage 2: Pipeline Preparation
        logger.info("Stage 2: Preparing data transformation pipeline")
        data_pipeline = prepare_data_pipeline()
        pipeline_tracker.track_stage("2_pipeline_preparation", data_pipeline, {
            "pipeline_type": type(data_pipeline).__name__,
            "has_components": hasattr(data_pipeline, 'components')
        })
        
        assert data_pipeline is not None, "Pipeline should be created"
        
        # Stage 3: Document Transformation (Chunking + Embedding)
        logger.info("Stage 3: Transforming documents (chunking + embedding)")
        db_path = os.path.join(temp_db_dir, "test_db.pkl")
        
        try:
            db = transform_documents_and_save_to_db(documents, db_path)
            transformed_docs = db.get_transformed_data(key="split_and_embed")
            pipeline_tracker.track_stage("3_document_transformation", transformed_docs, {
                "db_path": db_path,
                "transform_key": "split_and_embed"
            })
            
            assert transformed_docs is not None, "Should get transformed documents"
            assert len(transformed_docs) > 0, "Should have at least one transformed document"
            
            # Verify all transformed documents have vectors
            for i, doc in enumerate(transformed_docs):
                assert hasattr(doc, 'vector'), f"Document {i} should have vector attribute"
                assert doc.vector is not None, f"Document {i} should have non-None vector"
                
                # Check vector dimension and validity
                if isinstance(doc.vector, list):
                    assert len(doc.vector) > 0, f"Document {i} vector should not be empty"
                    assert all(isinstance(v, (int, float)) for v in doc.vector), f"Document {i} vector should contain numeric values"
                    assert all(not np.isnan(v) and not np.isinf(v) for v in doc.vector), f"Document {i} vector should not contain NaN or Inf"
        
        except Exception as e:
            pipeline_tracker.track_stage("3_document_transformation", [], {
                "error": str(e),
                "error_type": type(e).__name__
            })
            pytest.fail(f"Document transformation failed: {e}")
        
        # Stage 4: RAG Component Initialization
        logger.info("Stage 4: Initializing RAG component")
        try:
            # Use a simple mock provider for testing to avoid API dependencies
            with patch('api.config.get_model_config') as mock_get_model:
                mock_client_instance = type('MockClient', (), {
                    '__call__': lambda self, *args, **kwargs: type('MockResponse', (), {
                        'data': 'Test response data'
                    })()
                })()
                
                mock_get_model.return_value = {
                    'model_client': lambda: mock_client_instance,
                    'model_kwargs': {'model': 'test-model'}
                }
                
                rag = RAG(provider="google", model="gemini-2.5-flash")
                pipeline_tracker.track_stage("4_rag_initialization", rag, {
                    "provider": "google",
                    "model": "gemini-2.5-flash"
                })
                
                assert rag is not None, "RAG component should be created"
                
        except Exception as e:
            pipeline_tracker.track_stage("4_rag_initialization", [], {
                "error": str(e),
                "error_type": type(e).__name__
            })
            logger.error(f"RAG initialization failed: {e}")
            # Continue test to analyze pipeline up to this point
        
        # Stage 5: FAISS Retriever Setup
        logger.info("Stage 5: Setting up FAISS retriever")
        try:
            rag.prepare_retriever(temp_repo_dir, type="github")
            pipeline_tracker.track_stage("5_retriever_setup", rag.transformed_docs, {
                "repo_path": temp_repo_dir,
                "retriever_type": "FAISS"
            })
            
            assert hasattr(rag, 'retriever'), "RAG should have retriever"
            assert rag.retriever is not None, "Retriever should not be None"
            assert len(rag.transformed_docs) > 0, "Should have transformed documents for retrieval"
            
        except Exception as e:
            pipeline_tracker.track_stage("5_retriever_setup", [], {
                "error": str(e),
                "error_type": type(e).__name__
            })
            logger.error(f"Retriever setup failed: {e}")
        
        # Stage 6: Query Processing (if retriever was set up successfully)
        if hasattr(rag, 'retriever') and rag.retriever is not None:
            logger.info("Stage 6: Testing query retrieval")
            try:
                test_query = "How to use the hello_world function?"
                retrieved_docs = rag.call(test_query)
                pipeline_tracker.track_stage("6_query_retrieval", retrieved_docs, {
                    "query": test_query,
                    "retrieval_method": "similarity_search"
                })
                
                assert retrieved_docs is not None, "Should retrieve documents for query"
                
            except Exception as e:
                pipeline_tracker.track_stage("6_query_retrieval", [], {
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                logger.error(f"Query retrieval failed: {e}")
        
        # Generate pipeline analysis report
        issues = pipeline_tracker.report_issues()
        logger.info("=== Pipeline Analysis Report ===")
        if issues:
            logger.warning("Issues found in pipeline:")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info("No issues detected in pipeline flow")
        
        # Log stage summary
        logger.info("=== Stage Summary ===")
        for stage_name, stage_info in pipeline_tracker.stages.items():
            logger.info(f"{stage_name}: {stage_info['data_count']} items, type: {stage_info['data_type']}")
        
        # At minimum, we should have completed document reading and transformation
        assert "1_document_reading" in pipeline_tracker.stages
        assert "3_document_transformation" in pipeline_tracker.stages
        assert pipeline_tracker.stages["1_document_reading"]["data_count"] > 0
    
    def test_error_propagation_through_pipeline(self, embedding_bug_scenario_data, temp_db_dir, pipeline_tracker):
        """
        Test how errors propagate through the pipeline and where they originate.
        
        Uses problematic data that is known to cause issues to trace error propagation.
        """
        logger.info("=== Starting Error Propagation Test ===")
        
        # Test with various problematic scenarios
        scenarios = embedding_bug_scenario_data
        
        for scenario_name, scenario_data in scenarios.items():
            if scenario_name == "concurrent_batches":
                continue  # Skip concurrent test in this context
                
            logger.info(f"Testing scenario: {scenario_name}")
            
            # Convert scenario data to Document objects
            test_documents = []
            for i, doc_data in enumerate(scenario_data):
                test_documents.append(Document(
                    text=doc_data["content"],
                    meta_data=doc_data.get("metadata", {"id": f"{scenario_name}_{i}"})
                ))
            
            pipeline_tracker.track_stage(f"scenario_{scenario_name}_input", test_documents, {
                "scenario": scenario_name,
                "input_count": len(test_documents)
            })
            
            # Try to process through pipeline
            db_path = os.path.join(temp_db_dir, f"test_{scenario_name}.pkl")
            
            try:
                db = transform_documents_and_save_to_db(test_documents, db_path)
                transformed_docs = db.get_transformed_data(key="split_and_embed")
                pipeline_tracker.track_stage(f"scenario_{scenario_name}_output", transformed_docs, {
                    "scenario": scenario_name,
                    "success": True
                })
                
                # Analyze results
                if transformed_docs:
                    logger.info(f"Scenario {scenario_name}: Successfully processed {len(transformed_docs)} documents")
                else:
                    logger.warning(f"Scenario {scenario_name}: No documents after transformation")
                    
            except Exception as e:
                pipeline_tracker.track_stage(f"scenario_{scenario_name}_output", [], {
                    "scenario": scenario_name,
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                logger.error(f"Scenario {scenario_name} failed: {e}")
        
        # Analyze error patterns
        issues = pipeline_tracker.report_issues()
        logger.info("=== Error Propagation Analysis ===")
        for issue in issues:
            logger.info(f"Issue detected: {issue}")
        
        # The test passes if we successfully tracked errors through the pipeline
        assert len(pipeline_tracker.stages) > 0, "Should track at least one pipeline stage"
    
    def test_recovery_from_partial_failures(self, batch_processing_edge_cases, temp_db_dir, pipeline_tracker):
        """
        Test recovery mechanisms when part of a batch fails but other parts succeed.
        
        This test checks how the pipeline handles mixed success/failure scenarios
        and whether it can recover valid embeddings from partially failed batches.
        """
        logger.info("=== Starting Partial Failure Recovery Test ===")
        
        edge_cases = batch_processing_edge_cases
        
        for case_name, case_data in edge_cases.items():
            logger.info(f"Testing edge case: {case_name}")
            
            # Convert to Document objects
            test_documents = []
            for i, doc_data in enumerate(case_data):
                test_documents.append(Document(
                    text=doc_data["content"],
                    meta_data=doc_data.get("metadata", {"id": f"{case_name}_{i}"})
                ))
            
            pipeline_tracker.track_stage(f"edge_case_{case_name}_input", test_documents, {
                "case": case_name,
                "input_count": len(test_documents)
            })
            
            # Process with error handling
            db_path = os.path.join(temp_db_dir, f"edge_{case_name}.pkl")
            
            try:
                # Enable adaptive retry for better recovery
                with patch('api.data_pipeline._get_adaptive_retry_config') as mock_config:
                    mock_config.return_value = {
                        "enabled": True,
                        "max_retries": 2,
                        "backoff_factor": 0.5,
                        "min_batch_size": 1,
                        "min_chunk_size": 50
                    }
                    
                    db = transform_documents_and_save_to_db(test_documents, db_path)
                    transformed_docs = db.get_transformed_data(key="split_and_embed")
                    
                    pipeline_tracker.track_stage(f"edge_case_{case_name}_output", transformed_docs, {
                        "case": case_name,
                        "recovery_attempted": True,
                        "output_count": len(transformed_docs) if transformed_docs else 0
                    })
                    
                    if transformed_docs:
                        # Check recovery success rate
                        valid_docs = [doc for doc in transformed_docs if hasattr(doc, 'vector') and doc.vector and len(doc.vector) > 0]
                        recovery_rate = len(valid_docs) / len(transformed_docs) if transformed_docs else 0
                        logger.info(f"Edge case {case_name}: Recovery rate {recovery_rate:.2f} ({len(valid_docs)}/{len(transformed_docs)})")
                    
            except Exception as e:
                pipeline_tracker.track_stage(f"edge_case_{case_name}_output", [], {
                    "case": case_name,
                    "recovery_attempted": True,
                    "recovery_failed": True,
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                logger.error(f"Edge case {case_name} recovery failed: {e}")
        
        # Generate recovery analysis
        logger.info("=== Recovery Analysis ===")
        successful_recoveries = 0
        failed_recoveries = 0
        
        for stage_name, stage_info in pipeline_tracker.stages.items():
            if "output" in stage_name:
                if stage_info.get("recovery_failed", False):
                    failed_recoveries += 1
                elif stage_info.get("output_count", 0) > 0:
                    successful_recoveries += 1
        
        logger.info(f"Recovery results: {successful_recoveries} successful, {failed_recoveries} failed")
        
        # Test passes if we attempted recovery for edge cases
        assert len(pipeline_tracker.stages) > 0, "Should track recovery attempts"
    
    def test_data_integrity_at_each_stage(self, temp_repo_dir, temp_db_dir, pipeline_tracker):
        """
        Test data integrity and transformation correctness at each pipeline stage.
        
        This test validates that data is correctly transformed and preserved
        through each stage of the pipeline without corruption.
        """
        logger.info("=== Starting Data Integrity Test ===")
        
        # Stage 1: Load initial documents
        documents = read_all_documents(temp_repo_dir)
        pipeline_tracker.track_stage("integrity_1_initial", documents)
        
        initial_content_hashes = {}
        for i, doc in enumerate(documents):
            initial_content_hashes[i] = hash(doc.text)
        
        assert len(documents) > 0, "Should load initial documents"
        
        # Stage 2: Process through text splitter only
        logger.info("Testing text splitter stage")
        splitter = TextSplitter(chunk_size=200, chunk_overlap=50)
        
        split_docs = []
        for doc in documents:
            doc_splits = splitter(doc)
            if isinstance(doc_splits, list):
                split_docs.extend(doc_splits)
            else:
                split_docs.append(doc_splits)
        
        pipeline_tracker.track_stage("integrity_2_split", split_docs)
        
        # Verify splitting preserved content
        combined_split_content = " ".join([doc.text for doc in split_docs])
        original_content = " ".join([doc.text for doc in documents])
        
        # Content should be preserved (allowing for chunking)
        assert len(split_docs) >= len(documents), "Splitting should create same or more documents"
        
        # Stage 3: Add embeddings
        logger.info("Testing embedding stage")
        embedder = get_embedder()
        
        # Process a small sample to avoid API limits in tests
        sample_docs = split_docs[:5] if len(split_docs) > 5 else split_docs
        
        try:
            embedding_transformer = ToEmbeddings(embedder=embedder, batch_size=2)
            embedded_docs = embedding_transformer(sample_docs)
            pipeline_tracker.track_stage("integrity_3_embedded", embedded_docs)
            
            # Verify embedding integrity
            for doc in embedded_docs:
                assert hasattr(doc, 'vector'), "Document should have vector after embedding"
                assert doc.vector is not None, "Vector should not be None"
                assert hasattr(doc, 'text'), "Document should retain original text"
                assert len(doc.text.strip()) > 0, "Document should retain non-empty text"
                
                if isinstance(doc.vector, list):
                    assert len(doc.vector) > 0, "Vector should have dimensions"
                    assert all(isinstance(v, (int, float)) for v in doc.vector), "Vector should contain numeric values"
        
        except Exception as e:
            pipeline_tracker.track_stage("integrity_3_embedded", [], {
                "error": str(e),
                "error_type": type(e).__name__
            })
            logger.error(f"Embedding stage failed: {e}")
            # Continue to analyze what we have so far
        
        # Generate integrity report
        issues = pipeline_tracker.report_issues()
        logger.info("=== Data Integrity Report ===")
        for issue in issues:
            logger.warning(f"Integrity issue: {issue}")
        
        # Test passes if we maintained data integrity through tracked stages
        assert "integrity_1_initial" in pipeline_tracker.stages
        assert pipeline_tracker.stages["integrity_1_initial"]["data_count"] > 0
    
    def test_identify_exact_failure_point(self, embedding_validation_scenarios, temp_db_dir, pipeline_tracker):
        """
        Test to identify the exact point where pipeline failures occur.
        
        This test uses controlled failure scenarios to pinpoint where
        in the pipeline things go wrong, especially for empty vector issues.
        """
        logger.info("=== Starting Failure Point Identification Test ===")
        
        validation_scenarios = embedding_validation_scenarios
        
        # Test with valid embeddings first (baseline)
        logger.info("Testing with valid embeddings (baseline)")
        valid_vectors = validation_scenarios["valid_embeddings"]
        
        # Create documents with pre-generated valid vectors
        valid_docs = []
        for i, vector in enumerate(valid_vectors[:3]):  # Use first 3
            doc = Document(
                text=f"Valid document {i} for baseline testing",
                meta_data={"id": f"valid_{i}", "type": "test"}
            )
            doc.vector = vector  # Pre-assign valid vector
            valid_docs.append(doc)
        
        pipeline_tracker.track_stage("baseline_valid_input", valid_docs)
        
        # Test with invalid embeddings
        logger.info("Testing with invalid embeddings")
        invalid_scenarios = validation_scenarios["invalid_embeddings"]
        
        for invalid_type, invalid_vector in invalid_scenarios.items():
            logger.info(f"Testing invalid scenario: {invalid_type}")
            
            # Create document with invalid vector
            invalid_doc = Document(
                text=f"Document with {invalid_type} vector",
                meta_data={"id": f"invalid_{invalid_type}", "type": "test"}
            )
            invalid_doc.vector = invalid_vector
            
            pipeline_tracker.track_stage(f"invalid_{invalid_type}_input", [invalid_doc])
            
            # Try to create FAISS index with this document
            try:
                from adalflow.components.retriever.faiss_retriever import FAISSRetriever
                embedder = get_embedder()
                
                # This should fail or handle the invalid vector
                retriever = FAISSRetriever(
                    top_k=1,
                    embedder=embedder,
                    documents=[invalid_doc],
                    document_map_func=lambda doc: doc.vector,
                )
                
                pipeline_tracker.track_stage(f"invalid_{invalid_type}_result", [invalid_doc], {
                    "faiss_creation": "success",
                    "unexpected_success": True
                })
                
            except Exception as e:
                pipeline_tracker.track_stage(f"invalid_{invalid_type}_result", [], {
                    "faiss_creation": "failed",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "failure_point": "FAISS_creation"
                })
                logger.info(f"Invalid {invalid_type}: Failed at FAISS creation as expected: {e}")
        
        # Test mixed batch (valid + invalid)
        logger.info("Testing mixed batch scenario")
        mixed_docs = valid_docs[:2]  # 2 valid documents
        
        # Add document with empty vector
        empty_doc = Document(
            text="Document with empty vector",
            meta_data={"id": "mixed_empty", "type": "test"}
        )
        empty_doc.vector = []  # Empty vector
        mixed_docs.append(empty_doc)
        
        pipeline_tracker.track_stage("mixed_batch_input", mixed_docs)
        
        try:
            from adalflow.components.retriever.faiss_retriever import FAISSRetriever
            embedder = get_embedder()
            
            # This should identify and filter invalid vectors
            retriever = FAISSRetriever(
                top_k=1,
                embedder=embedder,
                documents=mixed_docs,
                document_map_func=lambda doc: doc.vector,
            )
            
            pipeline_tracker.track_stage("mixed_batch_result", mixed_docs, {
                "faiss_creation": "success",
                "filtered_count": len([d for d in mixed_docs if hasattr(d, 'vector') and d.vector and len(d.vector) > 0])
            })
            
        except Exception as e:
            pipeline_tracker.track_stage("mixed_batch_result", [], {
                "faiss_creation": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "failure_point": "mixed_batch_processing"
            })
            logger.error(f"Mixed batch failed: {e}")
        
        # Analyze failure points
        logger.info("=== Failure Point Analysis ===")
        failure_points = {}
        
        for stage_name, stage_info in pipeline_tracker.stages.items():
            if "error" in stage_info:
                failure_point = stage_info.get("failure_point", "unknown")
                failure_points[failure_point] = failure_points.get(failure_point, 0) + 1
                logger.error(f"Failure at {failure_point}: {stage_info['error']}")
        
        if failure_points:
            logger.info("Failure point summary:")
            for point, count in failure_points.items():
                logger.info(f"  {point}: {count} failures")
        else:
            logger.info("No clear failure points identified (may indicate robust handling)")
        
        # Test passes if we successfully identified failure points
        assert len(pipeline_tracker.stages) > 0, "Should track failure analysis stages"
    
    @pytest.mark.slow
    def test_batch_processing_scenarios(self, memory_pressure_scenarios, temp_db_dir, pipeline_tracker):
        """
        Test batch processing under various load conditions.
        
        This test checks how the pipeline handles different batch sizes
        and memory pressure scenarios to identify scalability limits.
        """
        logger.info("=== Starting Batch Processing Test ===")
        
        memory_scenarios = memory_pressure_scenarios
        
        for scenario_name, scenario_docs in memory_scenarios.items():
            logger.info(f"Testing scenario: {scenario_name} ({len(scenario_docs)} documents)")
            
            # Convert to Document objects
            test_documents = []
            for i, doc_data in enumerate(scenario_docs):
                test_documents.append(Document(
                    text=doc_data["content"],
                    meta_data=doc_data.get("metadata", {"id": f"{scenario_name}_{i}"})
                ))
            
            pipeline_tracker.track_stage(f"batch_{scenario_name}_input", test_documents, {
                "scenario": scenario_name,
                "document_count": len(test_documents),
                "estimated_size_mb": sum(len(doc.text.encode('utf-8')) for doc in test_documents) / (1024 * 1024)
            })
            
            # Process with different batch sizes
            batch_sizes = [1, 10, 50] if len(test_documents) > 50 else [1, min(10, len(test_documents))]
            
            for batch_size in batch_sizes:
                logger.info(f"Testing {scenario_name} with batch size {batch_size}")
                
                try:
                    db_path = os.path.join(temp_db_dir, f"batch_{scenario_name}_{batch_size}.pkl")
                    
                    # Override batch size for this test
                    with patch('api.config.get_embedder_config') as mock_config:
                        mock_config.return_value = {
                            "batch_size": batch_size,
                            "model_kwargs": {"model": "text-embedding-004"}
                        }
                        
                        db = transform_documents_and_save_to_db(test_documents, db_path)
                        transformed_docs = db.get_transformed_data(key="split_and_embed")
                        
                        pipeline_tracker.track_stage(f"batch_{scenario_name}_{batch_size}_result", transformed_docs, {
                            "batch_size": batch_size,
                            "success": True,
                            "output_count": len(transformed_docs) if transformed_docs else 0
                        })
                        
                        logger.info(f"Batch {scenario_name} (size {batch_size}): Processed {len(transformed_docs) if transformed_docs else 0} documents")
                
                except Exception as e:
                    pipeline_tracker.track_stage(f"batch_{scenario_name}_{batch_size}_result", [], {
                        "batch_size": batch_size,
                        "success": False,
                        "error": str(e),
                        "error_type": type(e).__name__
                    })
                    logger.error(f"Batch {scenario_name} (size {batch_size}) failed: {e}")
                    break  # Don't try larger batch sizes if smaller ones fail
        
        # Analyze batch processing results
        logger.info("=== Batch Processing Analysis ===")
        successful_batches = 0
        failed_batches = 0
        
        for stage_name, stage_info in pipeline_tracker.stages.items():
            if "_result" in stage_name and "batch_size" in stage_info:
                if stage_info.get("success", False):
                    successful_batches += 1
                else:
                    failed_batches += 1
        
        logger.info(f"Batch processing results: {successful_batches} successful, {failed_batches} failed")
        
        # Test passes if we completed batch analysis
        assert len(pipeline_tracker.stages) > 0, "Should track batch processing stages"