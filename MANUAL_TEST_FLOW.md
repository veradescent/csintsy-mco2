# Manual Test Flow for Family Relationship Chatbot - Intelligent Behavior & Sound Relationships

## Overview
This document provides a focused manual testing procedure to validate the family relationship chatbot's **intelligent behavior** and **sound relationship detection** as specified in the project requirements. The tests focus on the chatbot's ability to infer relationships and detect impossible scenarios.

## Prerequisites
1. Ensure the chatbot is running (`python app.py`)
2. Open the application in a web browser (http://localhost:8000)
3. Navigate to the menu chat interface

## Test Set 1: Intelligent Relationship Inference

### Test Case 1.1: Grandfather Inference (From PDF Example)
**Objective**: Verify the chatbot can infer grandfather relationship without explicit statement
**Steps**:
1. Add: "Bob is the father of Alice."
2. Add: "Alice is the mother of John."
3. Query: "Is Bob a grandfather of John?"
**Expected Result**: Should return "Yes!" (inferring the grandfather relationship)

### Test Case 1.2: Grandmother Inference
**Objective**: Verify the chatbot can infer grandmother relationship
**Steps**:
1. Add: "Diana is the mother of Eve."
2. Add: "Eve is the mother of Frank."
3. Query: "Is Diana a grandmother of Frank?"
**Expected Result**: Should return "Yes!" (inferring the grandmother relationship)

### Test Case 1.3: Uncle/Aunt Inference
**Objective**: Verify the chatbot can infer uncle/aunt relationships
**Steps**:
1. Add: "Alice and Bob are siblings."
2. Add: "Bob is the father of Charlie."
3. Query: "Is Alice an aunt of Charlie?"
**Expected Result**: Should return "Yes!" (inferring the aunt relationship)

### Test Case 1.4: Cousin Inference
**Objective**: Verify the chatbot can infer cousin relationships
**Steps**:
1. Add: "Alice and Bob are siblings."
2. Add: "Charlie and Diana are siblings."
3. Add: "Alice is the mother of Eve."
4. Add: "Charlie is the father of Frank."
5. Query: "Are Eve and Frank cousins?"
**Expected Result**: Should return "Yes!" (inferring the cousin relationship)

### Test Case 1.5: Sibling Inference from Parents
**Objective**: Verify the chatbot can infer siblings from shared parents
**Steps**:
1. Add: "Alice and Bob are the parents of Charlie."
2. Add: "Alice and Bob are the parents of Diana."
3. Query: "Are Charlie and Diana siblings?"
**Expected Result**: Should return "Yes!" (inferring the sibling relationship)

## Test Set 2: Gender Consistency Detection

### Test Case 2.1: Father Cannot Be Daughter (From PDF Example)
**Objective**: Verify detection of gender inconsistency
**Steps**:
1. Add: "Mark is the father of Patricia."
2. Try to add: "Mark is a daughter of Ann."
**Expected Result**: Should return "That's impossible!" (detecting gender inconsistency)

### Test Case 2.2: Mother Cannot Be Son
**Objective**: Verify detection of gender inconsistency
**Steps**:
1. Add: "Sarah is the mother of Tom."
2. Try to add: "Sarah is a son of John."
**Expected Result**: Should return "That's impossible!" (detecting gender inconsistency)

### Test Case 2.3: Brother Cannot Be Sister
**Objective**: Verify detection of gender inconsistency
**Steps**:
1. Add: "John is a brother of Mary."
2. Try to add: "John is a sister of Mary."
**Expected Result**: Should return "That's impossible!" (detecting gender inconsistency)

### Test Case 2.4: Daughter Cannot Be Son
**Objective**: Verify detection of gender inconsistency
**Steps**:
1. Add: "Lisa is a daughter of Paul."
2. Try to add: "Lisa is a son of Paul."
**Expected Result**: Should return "That's impossible!" (detecting gender inconsistency)

## Test Set 3: Cyclical Relationship Detection

### Test Case 3.1: Three-Generation Cycle (From PDF Example)
**Objective**: Verify detection of cyclical relationships
**Steps**:
1. Add: "One is the father of Two."
2. Add: "Two is the father of Three."
3. Try to add: "Three is the father of One."
**Expected Result**: Should return "That's impossible!" (detecting cyclical relationship)

### Test Case 3.2: Direct Parent-Child Cycle
**Objective**: Verify detection of direct cyclical relationships
**Steps**:
1. Add: "Alice is the mother of Bob."
2. Try to add: "Bob is the mother of Alice."
**Expected Result**: Should return "That's impossible!" (detecting cyclical relationship)

### Test Case 3.3: Complex Multi-Generation Cycle
**Objective**: Verify detection of complex cyclical relationships
**Steps**:
1. Add: "Alice is the mother of Bob."
2. Add: "Bob is the father of Charlie."
3. Add: "Charlie is the mother of Diana."
4. Try to add: "Diana is the mother of Alice."
**Expected Result**: Should return "That's impossible!" (detecting cyclical relationship)

## Test Set 4: Self-Relationship Detection

### Test Case 4.1: Self-Parent Relationship (From PDF Example)
**Objective**: Verify detection of self-relationships
**Steps**:
1. Try to add: "Lea is the mother of Lea."
**Expected Result**: Should return "That's impossible!" (detecting self-relationship)

### Test Case 4.2: Self-Sibling Relationship
**Objective**: Verify detection of self-sibling relationships
**Steps**:
1. Try to add: "Alice and Alice are siblings."
**Expected Result**: Should return "That's impossible!" (detecting self-relationship)

### Test Case 4.3: Self-Child Relationship
**Objective**: Verify detection of self-child relationships
**Steps**:
1. Try to add: "Bob is a child of Bob."
**Expected Result**: Should return "That's impossible!" (detecting self-relationship)

## Test Set 5: Complex Intelligent Inferences

### Test Case 5.1: Step-Relationship Inference
**Objective**: Verify inference of step-relationships
**Steps**:
1. Add: "Alice and Bob are the parents of Charlie."
2. Add: "Bob and Diana are the parents of Eve."
3. Add: "Charlie is a son of Bob."
3. Query: "Is Charlie a stepbrother of Eve?"
**Expected Result**: Should return "Yes!" (inferring step-relationship)

### Test Case 5.2: Half-Sibling Inference
**Objective**: Verify inference of half-sibling relationships
**Steps**:
1. Add: "Alice is the mother of Bob."
2. Add: "Charlie is the father of Bob."
3. Add: "Alice is the mother of Diana."
4. Add: "Frank is the father of Diana."
5. Query: "Are Bob and Diana half-siblings?"
**Expected Result**: Should return "Yes!" (inferring half-sibling relationship)

### Test Case 5.3: In-Law Relationship Inference
**Objective**: Verify inference of in-law relationships
**Steps**:
1. Add: "Alice and Bob are siblings."
2. Add: "Bob and Charlie are married."
3. Query: "Is Alice a sister-in-law of Charlie?"
**Expected Result**: Should return "Yes!" (inferring in-law relationship)

## Test Set 6: Complex Impossible Scenarios

### Test Case 6.1: Incestual Relationship Detection
**Objective**: Verify detection of incestual relationships
**Steps**:
1. Add: "Alice is the mother of Bob."
2. Add: "Bob is the mother of Charlie."
3. Try to add: "Alice is the mother of Charlie."
**Expected Result**: Should return "That's impossible!" (detecting incestual relationship)

### Test Case 6.2: Multiple Parent Contradiction
**Objective**: Verify detection of conflicting parent relationships
**Steps**:
1. Add: "Alice is the mother of Bob."
2. Add: "Charlie is the mother of Bob."
3. Try to add: "Alice and Charlie are not the same person."
**Expected Result**: Should detect the contradiction or prevent it

### Test Case 6.3: Sibling-Parent Contradiction
**Objective**: Verify detection of sibling-parent contradictions
**Steps**:
1. Add: "Alice and Bob are siblings."
2. Try to add: "Alice is the mother of Bob."
**Expected Result**: Should return "That's impossible!" (detecting contradiction)

## Test Set 7: Query Intelligence

### Test Case 7.1: Complex Family Tree Query
**Objective**: Verify intelligent querying of complex relationships
**Steps**:
1. Build a complex family tree with multiple generations
2. Query: "Who are all the grandchildren of Alice?"
**Expected Result**: Should return all inferred grandchildren

### Test Case 7.2: Relationship Chain Query
**Objective**: Verify querying through relationship chains
**Steps**:
1. Add: "Alice is the mother of Bob."
2. Add: "Bob is the father of Charlie."
3. Add: "Charlie is the father of Diana."
4. Query: "Is Alice a great-grandmother of Diana?"
**Expected Result**: Should return "Yes!" (inferring great-grandmother relationship)

### Test Case 7.3: Negative Relationship Query
**Objective**: Verify intelligent negative relationship detection
**Steps**:
1. Add: "Alice is the mother of Bob."
2. Add: "Charlie is the mother of Diana."
3. Query: "Are Bob and Diana siblings?"
**Expected Result**: Should return "No!" (correctly identifying they're not siblings)

## Test Set 8: Edge Cases and Robustness

### Test Case 8.1: Large Family Tree
**Objective**: Verify system handles large family trees intelligently
**Steps**:
1. Add 15-20 relationships creating a complex family tree
2. Test various queries on the tree
3. Verify all inferences work correctly
**Expected Result**: System should handle large trees without errors

### Test Case 8.2: Relationship Updates
**Objective**: Verify intelligent behavior when relationships are updated
**Steps**:
1. Add: "Alice is the mother of Bob."
2. Add: "Bob is the father of Charlie."
3. Query: "Is Alice a grandmother of Charlie?" (should return Yes)
4. Remove or modify the relationship between Bob and Charlie
5. Query again: "Is Alice a grandmother of Charlie?"
**Expected Result**: Should update the answer based on current relationships

## Success Criteria for Intelligent Behavior

The chatbot should demonstrate intelligent behavior by:

1. **Inferring Relationships**: Automatically deducing relationships not explicitly stated
2. **Detecting Impossibilities**: Identifying relationships that violate real-world logic
3. **Maintaining Consistency**: Ensuring all relationships in the knowledge base are logically consistent
4. **Providing Accurate Queries**: Answering questions based on both explicit and inferred relationships
5. **Handling Complex Scenarios**: Managing multi-generational and complex family structures

## Expected Intelligent Behaviors (From PDF)

1. **Grandfather Inference**: Should infer grandfather relationship from father + mother chain
2. **Gender Consistency**: Should detect when someone is assigned conflicting gender roles
3. **Cyclical Detection**: Should prevent impossible ancestor-descendant cycles
4. **Self-Relationship Prevention**: Should prevent relationships where someone relates to themselves
5. **Sound Relationship Logic**: All relationships should follow real-world family logic

## Notes for Testing

1. **Focus on Logic**: Don't test name validation - focus on relationship logic
2. **Test Inference**: Verify the chatbot can deduce relationships not explicitly stated
3. **Test Impossibilities**: Verify the chatbot catches impossible scenarios
4. **Test Complex Scenarios**: Build complex family trees to test robustness
5. **Document Unexpected Behavior**: Note any cases where the chatbot doesn't behave intelligently

## Reporting Issues

When reporting issues with intelligent behavior:
1. Note the specific test case and scenario
2. Describe what relationship was being tested
3. Include the actual vs expected intelligent behavior
4. Note if the issue is with inference, impossibility detection, or query accuracy
5. Include the sequence of relationships that led to the issue 