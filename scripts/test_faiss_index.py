#!/usr/bin/env python3
"""
FAISS index testing script for validating embedding compatibility.

This script tests that:
- FAISS index creation works with 768-dimensional vectors
- Empty vectors cause expected failures
- Valid embeddings can be successfully indexed and searched
- Provides clear pass/fail status

Usage:
    python scripts/test_faiss_index.py
    python scripts/test_faiss_index.py --test-empty-vectors
    python scripts/test_faiss_index.py --verbose
    python scripts/test_faiss_index.py --help
"""

import argparse
import sys
import asyncio
import logging
import tempfile
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np

# Add the api directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

try:
    import faiss
except ImportError:
    print("Error: FAISS library not available. Install with: pip install faiss-cpu")
    sys.exit(1)

try:
    from google_embedding_client import GoogleEmbeddingClient
    from adalflow.core.types import ModelType
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FAISSIndexTester:
    """Tester for FAISS index operations with embeddings."""
    
    def __init__(self):
        self.embedding_client = GoogleEmbeddingClient()
        self.expected_dimension = 768
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': []
        }
    
    def log_test_result(self, test_name: str, passed: bool, details: str = "", error: Optional[Exception] = None):
        """Log a test result."""
        self.test_results['total_tests'] += 1
        if passed:
            self.test_results['passed_tests'] += 1
            logger.info(f"✅ PASS: {test_name}")
        else:
            self.test_results['failed_tests'] += 1
            logger.error(f"❌ FAIL: {test_name}")
            if details:
                logger.error(f"   Details: {details}")
            if error:
                logger.error(f"   Error: {str(error)}")
        
        self.test_results['test_details'].append({
            'name': test_name,
            'passed': passed,
            'details': details,
            'error': str(error) if error else None
        })
    
    def test_faiss_basic_operations(self) -> bool:
        """Test basic FAISS operations with synthetic vectors."""
        try:
            # Create a simple flat index
            index = faiss.IndexFlatL2(self.expected_dimension)
            
            # Generate some random vectors
            n_vectors = 10
            vectors = np.random.rand(n_vectors, self.expected_dimension).astype('float32')
            
            # Add vectors to index
            index.add(vectors)
            
            # Verify the vectors were added
            if index.ntotal != n_vectors:
                self.log_test_result(
                    "Basic FAISS operations", 
                    False, 
                    f"Expected {n_vectors} vectors, got {index.ntotal}"
                )
                return False
            
            # Test search
            k = 3
            query = vectors[0:1]  # Use first vector as query
            distances, indices = index.search(query, k)
            
            # The first result should be the query vector itself (distance ~0)
            if distances[0][0] > 1e-5:  # Allow for small floating point errors
                self.log_test_result(
                    "Basic FAISS operations", 
                    False, 
                    f"Self-search distance too large: {distances[0][0]}"
                )
                return False
            
            self.log_test_result("Basic FAISS operations", True)
            return True
            
        except Exception as e:
            self.log_test_result("Basic FAISS operations", False, error=e)
            return False
    
    def test_empty_vector_failure(self) -> bool:
        """Test that empty vectors cause expected failures in FAISS."""
        try:
            index = faiss.IndexFlatL2(self.expected_dimension)
            
            # Try to add an empty vector - this should fail
            empty_vector = np.array([]).astype('float32').reshape(0, self.expected_dimension)
            
            try:
                index.add(empty_vector)
                # If we get here, the test failed - empty vectors should not be accepted
                self.log_test_result(
                    "Empty vector rejection", 
                    False, 
                    "FAISS accepted empty vectors when it should have failed"
                )
                return False
            except Exception:
                # This is expected - empty vectors should cause an error
                pass
            
            # Try with a zero-length array in a different way
            try:
                # Create array with wrong shape (0 vectors)
                no_vectors = np.array([]).astype('float32').reshape(0, self.expected_dimension)
                index.add(no_vectors)
                # This might succeed (adding 0 vectors), that's okay
            except Exception:
                pass
            
            # Try with a vector of wrong dimensions (this should fail)
            try:
                wrong_dim_vector = np.random.rand(1, self.expected_dimension - 100).astype('float32')
                index.add(wrong_dim_vector)
                self.log_test_result(
                    "Empty vector rejection", 
                    False, 
                    "FAISS accepted wrong-dimension vectors when it should have failed"
                )
                return False
            except Exception:
                # This is expected - wrong dimensions should cause an error
                pass
            
            self.log_test_result("Empty vector rejection", True)
            return True
            
        except Exception as e:
            self.log_test_result("Empty vector rejection", False, error=e)
            return False
    
    def test_768_dimension_vectors(self) -> bool:
        """Test FAISS with exactly 768-dimensional vectors."""
        try:
            # Create index with expected dimensions
            index = faiss.IndexFlatL2(self.expected_dimension)
            
            # Generate vectors with exact expected dimensions
            n_vectors = 5
            vectors = np.random.rand(n_vectors, self.expected_dimension).astype('float32')
            
            # Verify the vectors have correct shape
            if vectors.shape != (n_vectors, self.expected_dimension):
                self.log_test_result(
                    "768-dimensional vectors", 
                    False, 
                    f"Vector shape mismatch: {vectors.shape}"
                )
                return False
            
            # Add to index
            index.add(vectors)
            
            # Verify all vectors were added
            if index.ntotal != n_vectors:
                self.log_test_result(
                    "768-dimensional vectors", 
                    False, 
                    f"Not all vectors added: {index.ntotal}/{n_vectors}"
                )
                return False
            
            # Test that we can search and get reasonable results
            query = vectors[0:1]
            distances, indices = index.search(query, min(3, n_vectors))
            
            if len(distances[0]) == 0:
                self.log_test_result(
                    "768-dimensional vectors", 
                    False, 
                    "Search returned no results"
                )
                return False
            
            self.log_test_result("768-dimensional vectors", True)
            return True
            
        except Exception as e:
            self.log_test_result("768-dimensional vectors", False, error=e)
            return False
    
    async def test_real_embeddings(self, dry_run: bool = False) -> bool:
        """Test FAISS with real embeddings from GoogleEmbeddingClient."""
        if dry_run:
            logger.info("DRY RUN: Would test FAISS with real embeddings")
            self.log_test_result("Real embeddings (dry run)", True, "Skipped in dry run mode")
            return True
        
        try:
            # Generate some real embeddings
            test_texts = [
                "This is a test document for FAISS indexing.",
                "Another document to test embedding and search.",
                "Third document for comprehensive testing."
            ]
            
            logger.info(f"Generating embeddings for {len(test_texts)} texts...")
            
            # Get embeddings
            api_kwargs = self.embedding_client.convert_inputs_to_api_kwargs(
                input=test_texts,
                model_type=ModelType.EMBEDDER
            )
            output = self.embedding_client.call(api_kwargs, ModelType.EMBEDDER)
            
            if output.error:
                self.log_test_result(
                    "Real embeddings", 
                    False, 
                    f"Embedding generation failed: {output.error}"
                )
                return False
            
            # Check for empty vectors in the output
            for i, embedding_obj in enumerate(output.data):
                if not embedding_obj.embedding or len(embedding_obj.embedding) == 0:
                    self.log_test_result(
                        "Real embeddings", 
                        False, 
                        f"Empty embedding detected at index {i}"
                    )
                    return False
                
                if len(embedding_obj.embedding) != self.expected_dimension:
                    self.log_test_result(
                        "Real embeddings", 
                        False, 
                        f"Wrong embedding dimension at index {i}: {len(embedding_obj.embedding)}"
                    )
                    return False
            
            # Convert to numpy array for FAISS
            embeddings_array = np.array([
                emb.embedding for emb in output.data
            ]).astype('float32')
            
            # Create and test FAISS index
            index = faiss.IndexFlatL2(self.expected_dimension)
            index.add(embeddings_array)
            
            if index.ntotal != len(test_texts):
                self.log_test_result(
                    "Real embeddings", 
                    False, 
                    f"FAISS index count mismatch: {index.ntotal}/{len(test_texts)}"
                )
                return False
            
            # Test search with first embedding
            query = embeddings_array[0:1]
            distances, indices = index.search(query, len(test_texts))
            
            # First result should be the query itself
            if indices[0][0] != 0 or distances[0][0] > 1e-5:
                self.log_test_result(
                    "Real embeddings", 
                    False, 
                    f"Self-search failed: index={indices[0][0]}, distance={distances[0][0]}"
                )
                return False
            
            self.log_test_result("Real embeddings", True, f"Successfully indexed {len(test_texts)} real embeddings")
            return True
            
        except Exception as e:
            self.log_test_result("Real embeddings", False, error=e)
            return False
    
    def test_index_persistence(self) -> bool:
        """Test saving and loading FAISS index."""
        try:
            # Create an index with some data
            index = faiss.IndexFlatL2(self.expected_dimension)
            n_vectors = 5
            vectors = np.random.rand(n_vectors, self.expected_dimension).astype('float32')
            index.add(vectors)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.faiss', delete=False) as tmp_file:
                faiss.write_index(index, tmp_file.name)
                
                # Load the index back
                loaded_index = faiss.read_index(tmp_file.name)
                
                # Verify the loaded index has the same data
                if loaded_index.ntotal != index.ntotal:
                    self.log_test_result(
                        "Index persistence", 
                        False, 
                        f"Loaded index has different vector count: {loaded_index.ntotal} vs {index.ntotal}"
                    )
                    return False
                
                # Test search on loaded index
                query = vectors[0:1]
                distances, indices = loaded_index.search(query, 1)
                
                if distances[0][0] > 1e-5:
                    self.log_test_result(
                        "Index persistence", 
                        False, 
                        f"Search on loaded index failed: distance={distances[0][0]}"
                    )
                    return False
            
            # Clean up
            import os
            os.unlink(tmp_file.name)
            
            self.log_test_result("Index persistence", True)
            return True
            
        except Exception as e:
            self.log_test_result("Index persistence", False, error=e)
            return False
    
    def print_test_report(self):
        """Print a comprehensive test report."""
        print("\n" + "="*60)
        print("FAISS INDEX TEST REPORT")
        print("="*60)
        
        print(f"Total tests run: {self.test_results['total_tests']}")
        print(f"Tests passed: {self.test_results['passed_tests']}")
        print(f"Tests failed: {self.test_results['failed_tests']}")
        
        if self.test_results['total_tests'] > 0:
            success_rate = (self.test_results['passed_tests'] / self.test_results['total_tests']) * 100
            print(f"Success rate: {success_rate:.1f}%")
        
        print("\nDETAILED RESULTS:")
        for detail in self.test_results['test_details']:
            status = "✅ PASS" if detail['passed'] else "❌ FAIL"
            print(f"  {status}: {detail['name']}")
            if not detail['passed'] and detail['details']:
                print(f"    {detail['details']}")
            if not detail['passed'] and detail['error']:
                print(f"    Error: {detail['error']}")
        
        print("\nOVERALL STATUS:")
        if self.test_results['failed_tests'] == 0:
            print("🎉 ALL TESTS PASSED: FAISS indexing is working correctly!")
        else:
            print("🚨 SOME TESTS FAILED: FAISS indexing has issues that need attention!")


async def main():
    """Main function to run FAISS tests."""
    parser = argparse.ArgumentParser(
        description='Test FAISS index creation and operations with embeddings'
    )
    parser.add_argument(
        '--test-empty-vectors',
        action='store_true',
        help='Include tests for empty vector handling'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Skip tests that require API calls'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    tester = FAISSIndexTester()
    
    print("Starting FAISS index tests...")
    
    try:
        # Run all tests
        await asyncio.gather(
            asyncio.create_task(asyncio.to_thread(tester.test_faiss_basic_operations)),
            asyncio.create_task(asyncio.to_thread(tester.test_768_dimension_vectors)),
            asyncio.create_task(asyncio.to_thread(tester.test_index_persistence)),
            asyncio.create_task(tester.test_real_embeddings(args.dry_run))
        )
        
        if args.test_empty_vectors:
            await asyncio.to_thread(tester.test_empty_vector_failure)
        
        # Print results
        tester.print_test_report()
        
        # Return appropriate exit code
        if tester.test_results['failed_tests'] > 0:
            return 1
        else:
            return 0
            
    except KeyboardInterrupt:
        print("\nTesting interrupted by user.")
        return 130
    except Exception as e:
        print(f"\nUnexpected error during testing: {e}")
        logger.exception("Testing failed with exception")
        return 2


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))