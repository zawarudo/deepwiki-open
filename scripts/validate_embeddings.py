#!/usr/bin/env python3
"""
Validation script for checking embedding health and detecting empty vectors.

This script validates that:
- No empty vectors exist in embedding outputs
- All embeddings are 768-dimensional
- Provides statistics on embedding health
- Can be run as a quick validation check

Usage:
    python scripts/validate_embeddings.py --sample-text "test content"
    python scripts/validate_embeddings.py --batch-test 10
    python scripts/validate_embeddings.py --help
"""

import argparse
import sys
import asyncio
import logging
from typing import List, Dict, Any
from pathlib import Path

# Add the api directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

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


class EmbeddingValidator:
    """Validator for embedding health and quality checks."""
    
    def __init__(self):
        self.client = GoogleEmbeddingClient()
        self.expected_dimension = 768
        self.stats = {
            'total_tested': 0,
            'empty_vectors': 0,
            'wrong_dimensions': 0,
            'valid_embeddings': 0,
            'api_failures': 0
        }
    
    def validate_embedding_vector(self, embedding: List[float], index: int = -1) -> Dict[str, Any]:
        """
        Validate a single embedding vector.
        
        Args:
            embedding: The embedding vector to validate
            index: Optional index for tracking
            
        Returns:
            Dict containing validation results
        """
        result = {
            'index': index,
            'is_valid': False,
            'is_empty': False,
            'wrong_dimension': False,
            'dimension': len(embedding) if embedding else 0,
            'error': None
        }
        
        try:
            # Check for empty vector
            if not embedding or len(embedding) == 0:
                result['is_empty'] = True
                result['error'] = "Empty embedding vector detected"
                self.stats['empty_vectors'] += 1
                return result
            
            # Check for correct dimensions
            if len(embedding) != self.expected_dimension:
                result['wrong_dimension'] = True
                result['error'] = f"Wrong dimension: {len(embedding)}, expected {self.expected_dimension}"
                self.stats['wrong_dimensions'] += 1
                return result
            
            # Check for all zeros (potential issue)
            if all(x == 0.0 for x in embedding):
                result['error'] = "All-zero embedding vector detected"
                return result
            
            # Check for NaN or infinite values
            if any(not isinstance(x, (int, float)) or x != x or abs(x) == float('inf') for x in embedding):
                result['error'] = "Invalid values (NaN/Inf) in embedding vector"
                return result
            
            result['is_valid'] = True
            self.stats['valid_embeddings'] += 1
            
        except Exception as e:
            result['error'] = f"Validation error: {str(e)}"
        
        return result
    
    async def test_embedding_generation(self, texts: List[str], dry_run: bool = False) -> Dict[str, Any]:
        """
        Test embedding generation for given texts.
        
        Args:
            texts: List of texts to generate embeddings for
            dry_run: If True, don't actually call the API
            
        Returns:
            Dict containing test results
        """
        if dry_run:
            logger.info(f"DRY RUN: Would test embedding generation for {len(texts)} texts")
            return {'dry_run': True, 'text_count': len(texts)}
        
        results = {
            'total_texts': len(texts),
            'successful_embeddings': 0,
            'failed_embeddings': 0,
            'validation_results': [],
            'api_error': None
        }
        
        try:
            logger.info(f"Testing embedding generation for {len(texts)} texts...")
            
            # Convert to API kwargs format
            api_kwargs = self.client.convert_inputs_to_api_kwargs(
                input=texts,
                model_type=ModelType.EMBEDDER
            )
            
            # Call the embeddings API
            output = self.client.call(api_kwargs, ModelType.EMBEDDER)
            
            if output.error:
                results['api_error'] = output.error
                logger.warning(f"API returned error: {output.error}")
            
            # Validate each embedding
            for i, embedding_obj in enumerate(output.data):
                self.stats['total_tested'] += 1
                validation_result = self.validate_embedding_vector(
                    embedding_obj.embedding, i
                )
                results['validation_results'].append(validation_result)
                
                if validation_result['is_valid']:
                    results['successful_embeddings'] += 1
                else:
                    results['failed_embeddings'] += 1
                    logger.error(
                        f"Embedding {i} failed validation: {validation_result['error']}"
                    )
            
        except Exception as e:
            self.stats['api_failures'] += 1
            results['api_error'] = str(e)
            logger.error(f"Failed to generate embeddings: {e}")
        
        return results
    
    def print_validation_report(self, results: Dict[str, Any] = None):
        """Print a comprehensive validation report."""
        print("\n" + "="*60)
        print("EMBEDDING VALIDATION REPORT")
        print("="*60)
        
        if results and results.get('dry_run'):
            print(f"DRY RUN: Would test {results['text_count']} texts")
            return
        
        print(f"Total embeddings tested: {self.stats['total_tested']}")
        print(f"Valid embeddings: {self.stats['valid_embeddings']}")
        print(f"Empty vectors detected: {self.stats['empty_vectors']}")
        print(f"Wrong dimensions detected: {self.stats['wrong_dimensions']}")
        print(f"API failures: {self.stats['api_failures']}")
        
        if self.stats['total_tested'] > 0:
            success_rate = (self.stats['valid_embeddings'] / self.stats['total_tested']) * 100
            print(f"Success rate: {success_rate:.2f}%")
        
        # Health status
        print("\nHEALTH STATUS:")
        if self.stats['empty_vectors'] > 0:
            print("🚨 CRITICAL: Empty vectors detected! System is compromised.")
        elif self.stats['wrong_dimensions'] > 0:
            print("⚠️  WARNING: Wrong dimension vectors detected.")
        elif self.stats['api_failures'] > 0:
            print("⚠️  WARNING: API failures detected.")
        elif self.stats['valid_embeddings'] > 0:
            print("✅ HEALTHY: All tested embeddings are valid.")
        else:
            print("❓ UNKNOWN: No embeddings tested.")
        
        if results:
            print(f"\nLAST TEST BATCH:")
            print(f"  Texts processed: {results.get('total_texts', 0)}")
            print(f"  Successful: {results.get('successful_embeddings', 0)}")
            print(f"  Failed: {results.get('failed_embeddings', 0)}")
            
            if results.get('api_error'):
                print(f"  API Error: {results['api_error']}")


async def main():
    """Main function to run validation tests."""
    parser = argparse.ArgumentParser(
        description='Validate embedding generation and detect empty vectors'
    )
    parser.add_argument(
        '--sample-text',
        type=str,
        help='Test with a single sample text'
    )
    parser.add_argument(
        '--batch-test',
        type=int,
        default=0,
        help='Test with N sample texts (default: 0)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be tested without making API calls'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    validator = EmbeddingValidator()
    
    # Determine what to test
    test_texts = []
    
    if args.sample_text:
        test_texts = [args.sample_text]
    elif args.batch_test > 0:
        # Generate sample texts for batch testing
        test_texts = [
            f"This is test document number {i+1} for validation purposes. "
            f"It contains sample content to test embedding generation quality."
            for i in range(args.batch_test)
        ]
    else:
        # Default: test with a few standard samples
        test_texts = [
            "This is a test document for embedding validation.",
            "Another sample text to verify embedding generation works correctly.",
            "Testing with various types of content including numbers 123 and symbols !@#."
        ]
    
    print(f"Testing embedding validation with {len(test_texts)} texts...")
    
    try:
        results = await validator.test_embedding_generation(test_texts, args.dry_run)
        validator.print_validation_report(results)
        
        # Return appropriate exit code
        if validator.stats['empty_vectors'] > 0:
            print("\n🚨 CRITICAL FAILURE: Empty vectors detected!")
            return 2
        elif validator.stats['wrong_dimensions'] > 0 or validator.stats['api_failures'] > 0:
            print("\n⚠️  WARNING: Issues detected in embedding generation.")
            return 1
        else:
            print("\n✅ SUCCESS: All embeddings validated successfully.")
            return 0
            
    except KeyboardInterrupt:
        print("\nValidation interrupted by user.")
        return 130
    except Exception as e:
        print(f"\nUnexpected error during validation: {e}")
        logger.exception("Validation failed with exception")
        return 3


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))