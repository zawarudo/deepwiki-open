# Task 006: Documentation Validation Test Plan

## Test Objective
Validate that all documentation accurately reflects the standardized RAG contracts, provides clear integration guidance, and includes comprehensive troubleshooting information for the tuple unpacking fix.

## Test Scope

### Documentation Coverage Areas
1. **API Contracts**: RAG.call() return type specifications
2. **Integration Patterns**: Consumer usage examples
3. **Provider Configurations**: Embedder/retriever setup guides
4. **Error Handling**: Troubleshooting guides and error recovery
5. **Migration Guide**: Steps to update existing code

## Test Scenarios

### 1. API Contract Documentation Tests

#### Test 1.1: Return Type Specification Accuracy
**Objective**: Verify documented return types match implementation
**Steps**:
1. Review README.md RAG section for return type documentation
2. Compare with actual RAG.__call__() implementation
3. Verify tuple structure (answer: Optional[str], documents: List[Document])
4. Check type hints in code match documentation

**Expected Results**:
- Documentation shows: `Tuple[Optional[str], List[Document]]`
- Examples demonstrate both success and empty cases
- Type annotations are consistent

#### Test 1.2: Method Signature Documentation
**Objective**: Validate all RAG methods are documented
**Steps**:
1. List all public methods in RAG class
2. Check each method is documented with parameters
3. Verify return types for each method
4. Confirm deprecation notices for legacy patterns

**Expected Results**:
- 100% public method coverage
- Clear parameter descriptions
- Return type specifications for all methods

### 2. Integration Pattern Tests

#### Test 2.1: Consumer Code Examples
**Objective**: Ensure examples work without modification
**Steps**:
1. Copy example code from documentation
2. Create test file with example
3. Run example with mock RAG instance
4. Verify no tuple unpacking errors

**Test Code**:
```python
def test_documentation_example_websocket():
    """Test websocket integration example from docs"""
    # Example from docs
    rag = RAG(provider="openai", model="gpt-3.5-turbo")
    rag.prepare_retriever(documents)
    
    # Should work as documented
    answer, sources = rag("What is DeepWiki?")
    assert isinstance(answer, (str, type(None)))
    assert isinstance(sources, list)

def test_documentation_example_simple_chat():
    """Test simple_chat integration example from docs"""
    # Example from docs with error handling
    try:
        answer, sources = request_rag(query)
        if answer:
            return {"response": answer, "sources": sources}
        else:
            return {"response": "No answer found", "sources": []}
    except Exception as e:
        return {"error": str(e)}
```

#### Test 2.2: Normalization Helper Usage
**Objective**: Validate normalize_rag_result() examples
**Steps**:
1. Test with tuple input: `("answer", ["doc1", "doc2"])`
2. Test with list input: `["doc1", "doc2"]`
3. Test with None input
4. Test with malformed input

**Expected Results**:
- Helper handles all documented input types
- Examples show edge case handling
- Clear migration path from old to new pattern

### 3. Provider Configuration Tests

#### Test 3.1: Provider-Specific Setup Documentation
**Objective**: Verify each provider setup is accurately documented
**Providers to Test**:
- OpenAI
- Google Gemini
- Azure OpenAI
- Ollama
- OpenRouter

**Steps for Each Provider**:
1. Follow setup instructions exactly as written
2. Verify environment variables are documented
3. Test example configuration works
4. Check error messages match troubleshooting guide

**Test Matrix**:
| Provider | Env Vars | Example Works | Error Docs |
|----------|----------|---------------|------------|
| OpenAI | ✓ | ✓ | ✓ |
| Google | ✓ | ✓ | ✓ |
| Azure | ✓ | ✓ | ✓ |
| Ollama | ✓ | ✓ | ✓ |
| OpenRouter | ✓ | ✓ | ✓ |

#### Test 3.2: Embedder Configuration Examples
**Objective**: Test embedder adapter documentation
**Steps**:
1. Review embedder wrapper documentation
2. Test example adapter code
3. Verify FAISS integration examples
4. Check dimension mismatch handling docs

**Expected Results**:
- Clear adapter pattern explanation
- Working code examples
- Dimension validation documented

### 4. Error Handling Documentation Tests

#### Test 4.1: Common Error Scenarios
**Objective**: Validate troubleshooting guide completeness
**Error Scenarios**:
1. "not enough values to unpack"
2. "RAG object is not callable"
3. "Expected tuple, got list"
4. "Embedding dimension mismatch"
5. "No documents retrieved"

**Steps for Each Error**:
1. Locate error in troubleshooting guide
2. Verify root cause explanation is accurate
3. Test provided solution resolves issue
4. Check "Prevention" section exists

**Test Template**:
```python
def test_troubleshooting_tuple_unpack():
    """Verify tuple unpack error solution works"""
    # Simulate old pattern (should fail)
    with pytest.raises(ValueError, match="not enough values"):
        answer, sources = ["doc1", "doc2"]  # Wrong type
    
    # Apply documented solution
    result = normalize_rag_result(["doc1", "doc2"])
    answer, sources = result
    assert answer is None
    assert sources == ["doc1", "doc2"]
```

#### Test 4.2: Debug Logging Instructions
**Objective**: Test debug setup instructions work
**Steps**:
1. Follow logging configuration steps
2. Enable debug mode as documented
3. Trigger RAG call
4. Verify shape logs appear as described

**Expected Log Output**:
```
INFO: rag_call_start provider=openai model=gpt-3.5-turbo
DEBUG: embedder_return_shape type=tuple length=2
DEBUG: retriever_return_shape type=list length=5
INFO: rag_call_success return_shape=(str, list) status=success
```

### 5. Migration Guide Tests

#### Test 5.1: Step-by-Step Migration
**Objective**: Validate migration steps are complete and correct
**Steps**:
1. Start with code using old RAG pattern
2. Follow each migration step exactly
3. Run tests after each step
4. Verify no regressions

**Migration Checklist**:
- [ ] Step 1: Add normalize_rag_result import
- [ ] Step 2: Wrap existing RAG calls
- [ ] Step 3: Update error handling
- [ ] Step 4: Test with multiple providers
- [ ] Step 5: Remove legacy workarounds

#### Test 5.2: Backward Compatibility
**Objective**: Ensure documented compatibility claims are true
**Steps**:
1. Test old code patterns still work
2. Verify deprecation warnings appear
3. Check compatibility matrix is accurate
4. Test gradual migration approach

### 6. Code Example Validation Tests

#### Test 6.1: README Examples Compilation
**Objective**: All README code examples should run
**Steps**:
1. Extract all code blocks from README
2. Create test file for each example
3. Run with appropriate mocks
4. Verify no syntax or runtime errors

**Automation Script**:
```python
def test_readme_examples():
    """Extract and test all README code examples"""
    with open("README.md") as f:
        content = f.read()
    
    # Extract code blocks
    code_blocks = re.findall(r'```python\n(.*?)\n```', content, re.DOTALL)
    
    for i, code in enumerate(code_blocks):
        # Create test module
        exec_globals = {"RAG": MockRAG, "normalize_rag_result": mock_normalize}
        try:
            exec(code, exec_globals)
        except Exception as e:
            pytest.fail(f"README example {i} failed: {e}")
```

#### Test 6.2: Docstring Examples
**Objective**: Validate docstring examples work
**Steps**:
1. Use doctest to run all docstring examples
2. Verify output matches expected
3. Check examples cover main use cases

**Test Command**:
```bash
python -m doctest api/rag.py -v
python -m doctest api/utils/normalize.py -v
```

### 7. Cross-Reference Tests

#### Test 7.1: Internal Consistency
**Objective**: Documentation is internally consistent
**Checks**:
1. Function names match across all docs
2. Parameter names are consistent
3. Return types don't contradict
4. Version numbers align

#### Test 7.2: External References
**Objective**: External links and references are valid
**Steps**:
1. Check all URLs return 200 status
2. Verify API documentation links work
3. Test provider documentation links
4. Validate GitHub issue references

### 8. Accessibility and Clarity Tests

#### Test 8.1: Readability Assessment
**Objective**: Documentation is clear and understandable
**Criteria**:
- No undefined acronyms
- Technical terms explained
- Progressive disclosure (simple → complex)
- Clear section headings

#### Test 8.2: Search and Navigation
**Objective**: Users can find information quickly
**Tests**:
1. Search for "tuple unpack error" finds solution
2. Table of contents links work
3. Related sections are cross-linked
4. Index/glossary exists for technical terms

## Test Data Requirements

### Mock RAG Responses
```python
MOCK_SUCCESS = ("This is an answer", [
    Document(content="Doc 1", metadata={}),
    Document(content="Doc 2", metadata={})
])

MOCK_EMPTY = (None, [])

MOCK_ERROR = ValueError("not enough values to unpack")

MOCK_LEGACY = ["Doc 1", "Doc 2"]  # Old format
```

### Test Document Set
- Minimal valid document set (2 documents)
- Large document set (1000+ documents)
- Edge case documents (empty, very long, special chars)

## Test Execution Plan

### Phase 1: Static Analysis (30 min)
1. Run markdown linters
2. Check for broken links
3. Verify code block syntax
4. Spell check

### Phase 2: Example Testing (45 min)
1. Extract and run all examples
2. Test with each provider
3. Verify error cases
4. Check performance examples

### Phase 3: Integration Testing (30 min)
1. Follow setup guide on clean system
2. Test migration process
3. Verify troubleshooting steps
4. Test with real RAG instance

### Phase 4: User Testing (30 min)
1. Give docs to developer unfamiliar with system
2. Ask them to implement RAG integration
3. Note any confusion points
4. Update based on feedback

## Success Criteria

### Quantitative Metrics
- **100% example compilation**: All code examples run without errors
- **100% link validity**: No broken internal or external links
- **0 contradictions**: No conflicting information
- **< 5 min to solution**: Average time to find tuple unpack fix

### Qualitative Metrics
- **Clarity**: New developers understand within 15 minutes
- **Completeness**: No undocumented features or parameters
- **Actionability**: Each error has clear resolution steps
- **Maintainability**: Easy to update with new providers

## Risk Areas

### High Risk
1. **Outdated examples**: Code examples don't match current implementation
2. **Missing error cases**: Common errors not documented
3. **Provider differences**: Inconsistent behavior not explained

### Medium Risk
1. **Performance guidance**: No optimization tips
2. **Security notes**: Missing authentication best practices
3. **Version compatibility**: No version requirements listed

### Low Risk
1. **Formatting issues**: Inconsistent code style in examples
2. **Typos**: Minor spelling errors
3. **Verbose explanations**: Some sections too detailed

## Test Automation

### Continuous Testing
```yaml
name: Documentation Tests
on: [push, pull_request]

jobs:
  test-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Lint Markdown
        run: markdownlint README.md docs/
      
      - name: Check Links
        run: markdown-link-check README.md
      
      - name: Test Examples
        run: python test_documentation_examples.py
      
      - name: Validate API Docs
        run: python validate_api_documentation.py
```

### Manual Test Checklist
- [ ] README examples tested
- [ ] API documentation reviewed
- [ ] Migration guide followed
- [ ] Troubleshooting steps verified
- [ ] Provider setup tested
- [ ] Cross-references checked
- [ ] User feedback incorporated

## Deliverables
1. **Test Report**: Results of all test scenarios
2. **Documentation Updates**: List of required changes
3. **Example Test Suite**: Automated tests for all examples
4. **User Feedback Summary**: Results from user testing
5. **Documentation Standards**: Guidelines for future docs