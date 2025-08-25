#!/usr/bin/env python3
"""
Embedding regeneration script for data recovery after empty vector fix.

This script can:
- Regenerate embeddings for corrupted documents
- Process documents in batches
- Handle failures gracefully  
- Provide progress reporting
- Resume from interruptions
- Backup existing data before regeneration

Usage:
    python scripts/regenerate_embeddings.py --dry-run
    python scripts/regenerate_embeddings.py --batch-size 10
    python scripts/regenerate_embeddings.py --resume-from 50
    python scripts/regenerate_embeddings.py --validate-only
    python scripts/regenerate_embeddings.py --help
"""

import argparse
import sys
import asyncio
import logging
import json
import time
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

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


class EmbeddingRegenerator:
    """Tool for regenerating corrupted embeddings and data recovery."""
    
    def __init__(self, batch_size: int = 50, max_retries: int = 3):
        self.embedding_client = GoogleEmbeddingClient()
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.expected_dimension = 768
        
        # Progress tracking
        self.stats = {
            'total_documents': 0,
            'processed_documents': 0,
            'successful_embeddings': 0,
            'failed_embeddings': 0,
            'empty_vectors_found': 0,
            'start_time': None,
            'batches_completed': 0,
            'current_batch': 0
        }
        
        # State file for resumption
        self.state_file = Path('regeneration_state.json')
        self.backup_dir = Path('embedding_backups')
        
    def save_state(self, additional_data: Dict = None):
        """Save current regeneration state for resumption."""
        state = {
            'stats': self.stats.copy(),
            'timestamp': datetime.now().isoformat(),
            'batch_size': self.batch_size,
            'max_retries': self.max_retries
        }
        
        if additional_data:
            state.update(additional_data)
        
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            logger.debug(f"State saved to {self.state_file}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def load_state(self) -> Optional[Dict]:
        """Load previous regeneration state."""
        if not self.state_file.exists():
            return None
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            logger.info(f"Loaded previous state from {self.state_file}")
            return state
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return None
    
    def create_backup(self, data: Any, backup_name: str) -> bool:
        """Create a backup of current data before regeneration."""
        try:
            if not self.backup_dir.exists():
                self.backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"{backup_name}_{timestamp}.json"
            
            with open(backup_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Backup created: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    async def validate_existing_embeddings(self, embeddings_data: List[Dict]) -> Dict[str, Any]:
        """Validate existing embeddings to identify corruption."""
        logger.info("Validating existing embeddings...")
        
        validation_results = {
            'total_embeddings': len(embeddings_data),
            'empty_vectors': [],
            'wrong_dimensions': [],
            'valid_embeddings': [],
            'corrupted_indices': set()
        }
        
        for i, doc_data in enumerate(embeddings_data):
            embedding = doc_data.get('embedding', [])
            
            # Check for empty vectors
            if not embedding or len(embedding) == 0:
                validation_results['empty_vectors'].append(i)
                validation_results['corrupted_indices'].add(i)
                self.stats['empty_vectors_found'] += 1
                continue
            
            # Check for wrong dimensions
            if len(embedding) != self.expected_dimension:
                validation_results['wrong_dimensions'].append(i)
                validation_results['corrupted_indices'].add(i)
                continue
            
            # Check for invalid values
            try:
                if not all(isinstance(x, (int, float)) for x in embedding):
                    validation_results['corrupted_indices'].add(i)
                    continue
                if any(x != x or abs(x) == float('inf') for x in embedding):  # NaN or Inf check
                    validation_results['corrupted_indices'].add(i)
                    continue
            except Exception:
                validation_results['corrupted_indices'].add(i)
                continue
            
            validation_results['valid_embeddings'].append(i)
        
        logger.info(f"Validation complete:")
        logger.info(f"  Total embeddings: {validation_results['total_embeddings']}")
        logger.info(f"  Empty vectors: {len(validation_results['empty_vectors'])}")
        logger.info(f"  Wrong dimensions: {len(validation_results['wrong_dimensions'])}")
        logger.info(f"  Valid embeddings: {len(validation_results['valid_embeddings'])}")
        logger.info(f"  Total corrupted: {len(validation_results['corrupted_indices'])}")
        
        return validation_results
    
    async def regenerate_batch_embeddings(self, texts: List[str], indices: List[int], dry_run: bool = False) -> Dict[str, Any]:
        """Regenerate embeddings for a batch of texts."""
        if dry_run:
            logger.info(f"DRY RUN: Would regenerate embeddings for {len(texts)} texts")
            return {
                'dry_run': True,
                'batch_size': len(texts),
                'indices': indices,
                'successful': 0,
                'failed': 0
            }
        
        batch_results = {
            'batch_size': len(texts),
            'indices': indices,
            'successful': 0,
            'failed': 0,
            'new_embeddings': {},
            'errors': []
        }
        
        for retry_count in range(self.max_retries):
            try:
                logger.info(f"Generating embeddings for batch (attempt {retry_count + 1}/{self.max_retries})...")
                
                # Generate embeddings
                api_kwargs = self.embedding_client.convert_inputs_to_api_kwargs(
                    input=texts,
                    model_type=ModelType.EMBEDDER
                )
                output = self.embedding_client.call(api_kwargs, ModelType.EMBEDDER)
                
                if output.error:
                    logger.warning(f"API returned error on attempt {retry_count + 1}: {output.error}")
                    if retry_count == self.max_retries - 1:
                        batch_results['errors'].append(f"Final attempt failed: {output.error}")
                        break
                    await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                    continue
                
                # Process the embeddings
                for i, embedding_obj in enumerate(output.data):
                    doc_index = indices[i]
                    
                    # Validate the embedding
                    if (not embedding_obj.embedding or 
                        len(embedding_obj.embedding) == 0 or 
                        len(embedding_obj.embedding) != self.expected_dimension):
                        logger.error(f"Generated invalid embedding for document {doc_index}")
                        batch_results['failed'] += 1
                        batch_results['errors'].append(f"Invalid embedding generated for document {doc_index}")
                        continue
                    
                    # Store the valid embedding
                    batch_results['new_embeddings'][doc_index] = embedding_obj.embedding
                    batch_results['successful'] += 1
                    self.stats['successful_embeddings'] += 1
                
                logger.info(f"Batch completed: {batch_results['successful']}/{len(texts)} successful")
                break
                
            except Exception as e:
                logger.error(f"Error in batch regeneration attempt {retry_count + 1}: {e}")
                if retry_count == self.max_retries - 1:
                    batch_results['errors'].append(f"Final attempt exception: {str(e)}")
                    batch_results['failed'] = len(texts) - batch_results['successful']
                else:
                    await asyncio.sleep(2 ** retry_count)  # Exponential backoff
        
        self.stats['failed_embeddings'] += batch_results['failed']
        return batch_results
    
    async def regenerate_corrupted_embeddings(
        self, 
        documents_data: List[Dict], 
        corrupted_indices: Set[int],
        dry_run: bool = False,
        resume_from: int = 0
    ) -> Dict[str, Any]:
        """Regenerate embeddings for all corrupted documents."""
        
        # Filter to only corrupted documents that need regeneration
        docs_to_process = [
            (i, doc) for i, doc in enumerate(documents_data) 
            if i in corrupted_indices and i >= resume_from
        ]
        
        if not docs_to_process:
            logger.info("No documents need regeneration.")
            return {'success': True, 'processed': 0, 'batches': []}
        
        logger.info(f"Starting regeneration for {len(docs_to_process)} documents...")
        if resume_from > 0:
            logger.info(f"Resuming from document index {resume_from}")
        
        self.stats['total_documents'] = len(docs_to_process)
        self.stats['start_time'] = time.time()
        
        regeneration_results = {
            'success': True,
            'processed': 0,
            'batches': [],
            'updated_documents': {},
            'errors': []
        }
        
        # Process in batches
        for batch_start in range(0, len(docs_to_process), self.batch_size):
            batch_end = min(batch_start + self.batch_size, len(docs_to_process))
            batch_docs = docs_to_process[batch_start:batch_end]
            
            self.stats['current_batch'] = batch_start // self.batch_size + 1
            total_batches = (len(docs_to_process) + self.batch_size - 1) // self.batch_size
            
            logger.info(f"Processing batch {self.stats['current_batch']}/{total_batches}")
            
            # Extract texts and indices for this batch
            texts = [doc['text'] for _, doc in batch_docs if doc.get('text')]
            indices = [i for i, doc in batch_docs if doc.get('text')]
            
            if not texts:
                logger.warning(f"No valid texts found in batch {self.stats['current_batch']}")
                continue
            
            # Regenerate embeddings for this batch
            batch_results = await self.regenerate_batch_embeddings(texts, indices, dry_run)
            regeneration_results['batches'].append(batch_results)
            
            # Update documents with new embeddings
            if not dry_run and batch_results['new_embeddings']:
                for doc_index, new_embedding in batch_results['new_embeddings'].items():
                    documents_data[doc_index]['embedding'] = new_embedding
                    regeneration_results['updated_documents'][doc_index] = new_embedding
            
            # Update progress
            self.stats['processed_documents'] += len(batch_docs)
            self.stats['batches_completed'] += 1
            regeneration_results['processed'] += len(batch_docs)
            
            # Save progress state
            self.save_state({
                'resume_from': batch_end + resume_from,
                'batch_results': batch_results
            })
            
            # Report progress
            elapsed_time = time.time() - self.stats['start_time']
            progress_pct = (self.stats['processed_documents'] / self.stats['total_documents']) * 100
            logger.info(f"Progress: {progress_pct:.1f}% ({self.stats['processed_documents']}/{self.stats['total_documents']}) - {elapsed_time:.1f}s elapsed")
            
            # Small delay to be gentle on the API
            if not dry_run:
                await asyncio.sleep(0.1)
        
        if regeneration_results['errors']:
            regeneration_results['success'] = False
        
        return regeneration_results
    
    def print_regeneration_report(self, results: Dict[str, Any]):
        """Print comprehensive regeneration report."""
        print("\n" + "="*60)
        print("EMBEDDING REGENERATION REPORT")
        print("="*60)
        
        if results.get('dry_run'):
            print("DRY RUN MODE - No actual regeneration performed")
            return
        
        print(f"Total documents processed: {results.get('processed', 0)}")
        print(f"Successfully regenerated: {self.stats['successful_embeddings']}")
        print(f"Failed regenerations: {self.stats['failed_embeddings']}")
        print(f"Empty vectors found: {self.stats['empty_vectors_found']}")
        
        if self.stats['start_time']:
            elapsed_time = time.time() - self.stats['start_time']
            print(f"Total time: {elapsed_time:.1f} seconds")
            
            if self.stats['processed_documents'] > 0:
                avg_time = elapsed_time / self.stats['processed_documents']
                print(f"Average time per document: {avg_time:.2f} seconds")
        
        print(f"Batches completed: {self.stats['batches_completed']}")
        
        # Status
        print("\nSTATUS:")
        if results['success']:
            if self.stats['failed_embeddings'] == 0:
                print("🎉 SUCCESS: All embeddings regenerated successfully!")
            else:
                print("⚠️  PARTIAL SUCCESS: Some embeddings failed to regenerate.")
        else:
            print("🚨 FAILURE: Regeneration encountered significant errors.")
        
        # Batch details
        if results.get('batches'):
            print(f"\nBATCH DETAILS:")
            for i, batch in enumerate(results['batches'], 1):
                if batch.get('dry_run'):
                    print(f"  Batch {i}: Would process {batch['batch_size']} documents")
                else:
                    success_rate = (batch['successful'] / batch['batch_size']) * 100 if batch['batch_size'] > 0 else 0
                    print(f"  Batch {i}: {batch['successful']}/{batch['batch_size']} successful ({success_rate:.1f}%)")


async def main():
    """Main function for embedding regeneration."""
    parser = argparse.ArgumentParser(
        description='Regenerate corrupted embeddings for data recovery'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Number of documents to process per batch (default: 50)'
    )
    parser.add_argument(
        '--resume-from',
        type=int,
        default=0,
        help='Resume regeneration from specific document index'
    )
    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='Maximum retries for failed API calls (default: 3)'
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate existing embeddings, do not regenerate'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be regenerated without making changes'
    )
    parser.add_argument(
        '--input-file',
        type=str,
        help='JSON file containing embeddings data to process'
    )
    parser.add_argument(
        '--output-file',
        type=str,
        help='JSON file to save regenerated embeddings data'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    regenerator = EmbeddingRegenerator(
        batch_size=args.batch_size,
        max_retries=args.max_retries
    )
    
    # For demo purposes, create sample corrupted data if no input file specified
    if not args.input_file:
        logger.warning("No input file specified. Creating sample data for demonstration.")
        sample_documents = [
            {"text": "This is document 1 with corrupted embedding.", "embedding": []},  # Empty
            {"text": "Document 2 has wrong dimensions.", "embedding": [0.1] * 512},  # Wrong size
            {"text": "Document 3 is valid.", "embedding": [0.1] * 768},  # Valid
            {"text": "Document 4 also corrupted.", "embedding": []},  # Empty
            {"text": "Document 5 has valid embedding.", "embedding": [0.2] * 768},  # Valid
        ]
    else:
        # Load actual data
        try:
            with open(args.input_file, 'r') as f:
                sample_documents = json.load(f)
            logger.info(f"Loaded {len(sample_documents)} documents from {args.input_file}")
        except Exception as e:
            logger.error(f"Failed to load input file: {e}")
            return 1
    
    try:
        # Validate existing embeddings
        validation_results = await regenerator.validate_existing_embeddings(sample_documents)
        
        if args.validate_only:
            print("\nValidation Results:")
            print(f"Total embeddings: {validation_results['total_embeddings']}")
            print(f"Empty vectors: {len(validation_results['empty_vectors'])}")
            print(f"Wrong dimensions: {len(validation_results['wrong_dimensions'])}")
            print(f"Valid embeddings: {len(validation_results['valid_embeddings'])}")
            return 0 if len(validation_results['corrupted_indices']) == 0 else 1
        
        # Create backup if not dry run
        if not args.dry_run:
            if not regenerator.create_backup(sample_documents, "embeddings_pre_regeneration"):
                logger.warning("Failed to create backup - continuing anyway")
        
        # Regenerate corrupted embeddings
        regeneration_results = await regenerator.regenerate_corrupted_embeddings(
            sample_documents,
            validation_results['corrupted_indices'],
            args.dry_run,
            args.resume_from
        )
        
        # Save results if requested
        if args.output_file and not args.dry_run:
            try:
                with open(args.output_file, 'w') as f:
                    json.dump(sample_documents, f, indent=2)
                logger.info(f"Regenerated embeddings saved to {args.output_file}")
            except Exception as e:
                logger.error(f"Failed to save output file: {e}")
        
        # Print report
        regenerator.print_regeneration_report(regeneration_results)
        
        # Clean up state file on successful completion
        if regeneration_results['success'] and not args.dry_run:
            if regenerator.state_file.exists():
                regenerator.state_file.unlink()
        
        # Return exit code
        return 0 if regeneration_results['success'] else 1
        
    except KeyboardInterrupt:
        print("\nRegeneration interrupted by user.")
        logger.info("Saving current state before exit...")
        regenerator.save_state({'interrupted': True})
        return 130
    except Exception as e:
        logger.exception(f"Unexpected error during regeneration: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))