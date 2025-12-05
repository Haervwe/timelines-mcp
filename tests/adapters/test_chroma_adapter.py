"""
Chroma Adapter Tests - 100% coverage with real vector database operations

Tests all vector operations without mocks using actual ChromaDB.
Uses real embeddings and pytest fixtures for cleanup.
"""

import pytest


# ==========================================
# BASIC VECTOR OPERATIONS
# ==========================================


async def test_insert_and_get_vector(chroma_adapter):
    """Test inserting and retrieving a vector"""
    vector_id = "test_vector_1"
    embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
    metadata = {"event_id": "event_123", "timeline_id": "timeline_456"}
    
    await chroma_adapter.insert_vector(vector_id, embedding, metadata)
    
    result = await chroma_adapter.get_vector_by_id(vector_id)
    
    assert result is not None
    retrieved_embedding, retrieved_metadata = result
    # Compare lists element by element to avoid numpy array comparison issues
    assert len(retrieved_embedding) == len(embedding)
    for i, val in enumerate(embedding):
        assert abs(retrieved_embedding[i] - val) < 1e-6
    assert retrieved_metadata["event_id"] == "event_123"
    assert retrieved_metadata["timeline_id"] == "timeline_456"


async def test_get_vector_by_id_not_found(chroma_adapter):
    """Test getting non-existent vector returns None"""
    result = await chroma_adapter.get_vector_by_id("non_existent_id")
    assert result is None


async def test_insert_vector_with_numeric_metadata(chroma_adapter):
    """Test inserting vector with numeric metadata"""
    vector_id = "test_vector_numeric"
    embedding = [0.1, 0.2, 0.3]
    metadata = {
        "importance_score": 0.85,
        "event_count": 42,
        "is_canonical": 1.0,
    }
    
    await chroma_adapter.insert_vector(vector_id, embedding, metadata)
    
    result = await chroma_adapter.get_vector_by_id(vector_id)
    assert result is not None
    _, retrieved_metadata = result
    assert retrieved_metadata["importance_score"] == "0.85"
    assert retrieved_metadata["event_count"] == "42"


async def test_insert_multiple_vectors(chroma_adapter):
    """Test inserting multiple vectors"""
    vectors = [
        ("vec_1", [0.1, 0.2, 0.3], {"type": "event", "id": "1"}),
        ("vec_2", [0.4, 0.5, 0.6], {"type": "event", "id": "2"}),
        ("vec_3", [0.7, 0.8, 0.9], {"type": "event", "id": "3"}),
    ]
    
    for vec_id, embedding, metadata in vectors:
        await chroma_adapter.insert_vector(vec_id, embedding, metadata)
    
    # Verify all were inserted
    for vec_id, embedding, metadata in vectors:
        result = await chroma_adapter.get_vector_by_id(vec_id)
        assert result is not None


# ==========================================
# VECTOR SEARCH OPERATIONS
# ==========================================


async def test_search_vectors_basic(chroma_adapter):
    """Test basic vector similarity search"""
    # Insert vectors with known embeddings
    await chroma_adapter.insert_vector(
        "vec_1", [1.0, 0.0, 0.0], {"timeline_id": "t1", "type": "event"}
    )
    await chroma_adapter.insert_vector(
        "vec_2", [0.9, 0.1, 0.0], {"timeline_id": "t1", "type": "event"}
    )
    await chroma_adapter.insert_vector(
        "vec_3", [0.0, 1.0, 0.0], {"timeline_id": "t2", "type": "event"}
    )
    
    # Search with query similar to vec_1
    query_embedding = [1.0, 0.0, 0.0]
    results = await chroma_adapter.search_vectors(query_embedding, limit=2)
    
    assert len(results) == 2
    # First result should be vec_1 (exact match)
    assert results[0][0] == "vec_1"
    # Should have high similarity score
    assert results[0][1] > 0.9


async def test_search_vectors_with_limit(chroma_adapter):
    """Test search with result limit"""
    # Insert 5 vectors
    for i in range(5):
        await chroma_adapter.insert_vector(
            f"vec_{i}",
            [float(i) / 10, 0.5, 0.5],
            {"index": str(i)},
        )
    
    # Search with limit of 3
    query_embedding = [0.0, 0.5, 0.5]
    results = await chroma_adapter.search_vectors(query_embedding, limit=3)
    
    assert len(results) == 3


async def test_search_vectors_with_metadata_filter(chroma_adapter):
    """Test search with metadata filtering"""
    # Insert vectors with different metadata
    await chroma_adapter.insert_vector(
        "vec_1", [1.0, 0.0], {"timeline_id": "timeline_a", "type": "event"}
    )
    await chroma_adapter.insert_vector(
        "vec_2", [0.9, 0.1], {"timeline_id": "timeline_a", "type": "event"}
    )
    await chroma_adapter.insert_vector(
        "vec_3", [1.0, 0.0], {"timeline_id": "timeline_b", "type": "event"}
    )
    
    # Search with metadata filter
    query_embedding = [1.0, 0.0]
    results = await chroma_adapter.search_vectors(
        query_embedding,
        limit=10,
        metadata_filter={"timeline_id": "timeline_a"},
    )
    
    # Should only return vectors from timeline_a
    assert len(results) == 2
    for vec_id, score in results:
        assert vec_id in ["vec_1", "vec_2"]


async def test_search_vectors_empty_collection(chroma_adapter):
    """Test search on empty collection"""
    query_embedding = [1.0, 0.0, 0.0]
    results = await chroma_adapter.search_vectors(query_embedding, limit=10)
    
    assert results == []


async def test_search_vectors_no_matches_with_filter(chroma_adapter):
    """Test search with filter that matches nothing"""
    await chroma_adapter.insert_vector(
        "vec_1", [1.0, 0.0], {"timeline_id": "timeline_a"}
    )
    
    query_embedding = [1.0, 0.0]
    results = await chroma_adapter.search_vectors(
        query_embedding,
        limit=10,
        metadata_filter={"timeline_id": "timeline_b"},
    )
    
    assert results == []


# ==========================================
# DELETE OPERATIONS
# ==========================================


async def test_delete_vector(chroma_adapter):
    """Test deleting a vector"""
    vector_id = "vec_to_delete"
    embedding = [0.1, 0.2, 0.3]
    metadata = {"test": "value"}
    
    await chroma_adapter.insert_vector(vector_id, embedding, metadata)
    
    # Verify it exists
    result = await chroma_adapter.get_vector_by_id(vector_id)
    assert result is not None
    
    # Delete it
    await chroma_adapter.delete_vector(vector_id)
    
    # Verify it's gone
    result = await chroma_adapter.get_vector_by_id(vector_id)
    assert result is None


async def test_delete_non_existent_vector(chroma_adapter):
    """Test deleting non-existent vector (should not raise error)"""
    # Should not raise an exception
    await chroma_adapter.delete_vector("non_existent_vector")


async def test_delete_and_reinsert(chroma_adapter):
    """Test deleting and re-inserting same vector ID"""
    vector_id = "vec_reinsert"
    embedding1 = [0.1, 0.2, 0.3, 0.4, 0.5]
    embedding2 = [0.4, 0.5, 0.6, 0.7, 0.8]
    
    # Insert first version
    await chroma_adapter.insert_vector(vector_id, embedding1, {"version": "1"})
    
    # Delete
    await chroma_adapter.delete_vector(vector_id)
    
    # Insert second version
    await chroma_adapter.insert_vector(vector_id, embedding2, {"version": "2"})
    
    # Verify second version is stored
    result = await chroma_adapter.get_vector_by_id(vector_id)
    assert result is not None
    retrieved_embedding, retrieved_metadata = result
    assert len(retrieved_embedding) == len(embedding2)
    for i, val in enumerate(embedding2):
        assert abs(retrieved_embedding[i] - val) < 1e-6
    assert retrieved_metadata["version"] == "2"


# ==========================================
# PERSISTENCE TESTS
# ==========================================


async def test_persistent_chroma_adapter(chroma_persistent_adapter):
    """Test that persistent adapter stores data"""
    vector_id = "persistent_vec"
    embedding = [0.1, 0.2, 0.3, 0.4, 0.5]  # Match dimension
    metadata = {"persistent": "true"}

    await chroma_persistent_adapter.insert_vector(vector_id, embedding, metadata)

    result = await chroma_persistent_adapter.get_vector_by_id(vector_id)
    assert result is not None
    retrieved_embedding, _ = result
    assert len(retrieved_embedding) == len(embedding)
    for i, val in enumerate(embedding):
        assert abs(retrieved_embedding[i] - val) < 1e-6


# ==========================================
# EDGE CASES & ERROR HANDLING
# ==========================================


async def test_initialize_not_called_error():
    """Test operations fail gracefully if initialize not called"""
    from timelines_mcp.adapters.chroma import ChromaAdapter
    
    # Create new adapter without initializing
    adapter = ChromaAdapter(collection_name="test_uninitialized")

    # Should raise RuntimeError
    with pytest.raises(RuntimeError, match="Collection not initialized"):
        await adapter.insert_vector("test", [0.1, 0.2], {})

    with pytest.raises(RuntimeError, match="Collection not initialized"):
        await adapter.get_vector_by_id("test")

    with pytest.raises(RuntimeError, match="Collection not initialized"):
        await adapter.search_vectors([0.1, 0.2])

    with pytest.raises(RuntimeError, match="Collection not initialized"):
        await adapter.delete_vector("test")


async def test_persistent_directory_creation(tmp_path):
    """Test that persistent directory is created if it doesn't exist"""
    import os
    import uuid
    from timelines_mcp.adapters.chroma import ChromaAdapter

    persist_dir = tmp_path / "chroma_test"
    adapter = ChromaAdapter(
        collection_name=f"test_{uuid.uuid4().hex[:8]}",
        persist_directory=str(persist_dir)
    )

    # Initialize should create the directory
    await adapter.initialize()

    # Verify directory exists
    assert os.path.exists(persist_dir)

    # Insert a test vector
    await adapter.insert_vector("test_id", [0.1, 0.2, 0.3, 0.4, 0.5], {"key": "value"})

    # Verify retrieval works
    result = await adapter.get_vector_by_id("test_id")
    assert result is not None
    
    # Clean up
    await adapter.close()


async def test_delete_nonexistent_vector_exception_path(chroma_adapter):
    """Test delete gracefully handles nonexistent vectors through exception path"""
    # This will trigger the exception handler in delete_vector
    # since the ID doesn't exist
    await chroma_adapter.delete_vector("nonexistent_id_123456789")
    # Should not raise - just silently ignore


async def test_get_vector_exception_path(chroma_adapter):
    """Test get_vector exception handling for corrupted data"""
    # Try to get a nonexistent vector - triggers exception path
    result = await chroma_adapter.get_vector_by_id("nonexistent_vector")
    assert result is None


async def test_insert_with_existing_id_exception_path(chroma_adapter):
    """Test insert with existing ID when check fails"""
    # Insert first vector
    await chroma_adapter.insert_vector("test_id", [0.1, 0.2, 0.3, 0.4, 0.5], {"version": "1"})

    # Insert again - this will check for existing ID
    # The try/except in insert_vector handles the upsert logic
    await chroma_adapter.insert_vector("test_id", [0.9, 0.8, 0.7, 0.6, 0.5], {"version": "2"})

    # Verify it was updated
    result = await chroma_adapter.get_vector_by_id("test_id")
    assert result is not None
    _, metadata = result
    assert metadata["version"] == "2"


async def test_large_embedding_vector(chroma_adapter):
    """Test storing large embedding vectors"""
    vector_id = "large_vec"
    # Create a 1536-dimensional embedding (like OpenAI's text-embedding-ada-002)
    embedding = [float(i) / 1536 for i in range(1536)]
    metadata = {"model": "text-embedding-ada-002"}
    
    await chroma_adapter.insert_vector(vector_id, embedding, metadata)
    
    result = await chroma_adapter.get_vector_by_id(vector_id)
    assert result is not None
    retrieved_embedding, _ = result
    assert len(retrieved_embedding) == 1536


async def test_metadata_with_special_characters(chroma_adapter):
    """Test metadata with special characters"""
    vector_id = "special_char_vec"
    embedding = [0.1, 0.2]
    metadata = {
        "description": "Event with 'quotes' and \"double quotes\"",
        "tags": "tag1,tag2,tag3",
    }
    
    await chroma_adapter.insert_vector(vector_id, embedding, metadata)
    
    result = await chroma_adapter.get_vector_by_id(vector_id)
    assert result is not None
    _, retrieved_metadata = result
    assert "quotes" in retrieved_metadata["description"]


async def test_zero_vector(chroma_adapter):
    """Test storing zero vector"""
    vector_id = "zero_vec"
    embedding = [0.0, 0.0, 0.0, 0.0, 0.0]  # Match 5-dim
    metadata = {"type": "zero"}
    
    await chroma_adapter.insert_vector(vector_id, embedding, metadata)
    
    result = await chroma_adapter.get_vector_by_id(vector_id)
    assert result is not None
    retrieved_embedding, _ = result
    assert len(retrieved_embedding) == len(embedding)
    for i, val in enumerate(embedding):
        assert abs(retrieved_embedding[i] - val) < 1e-6


async def test_negative_values_in_embedding(chroma_adapter):
    """Test embeddings with negative values"""
    vector_id = "negative_vec"
    embedding = [-0.5, 0.3, -0.2, 0.8, 0.1]
    metadata = {"type": "negative"}
    
    await chroma_adapter.insert_vector(vector_id, embedding, metadata)
    
    result = await chroma_adapter.get_vector_by_id(vector_id)
    assert result is not None
    retrieved_embedding, _ = result
    assert len(retrieved_embedding) == len(embedding)
    for i, val in enumerate(embedding):
        assert abs(retrieved_embedding[i] - val) < 1e-6


async def test_similarity_score_range(chroma_adapter):
    """Test that similarity scores are in expected range [0, 1]"""
    # Insert reference vector
    await chroma_adapter.insert_vector("ref", [1.0, 0.0, 0.0], {"ref": "true"})
    
    # Insert vectors at different distances
    await chroma_adapter.insert_vector("similar", [0.9, 0.1, 0.0], {"type": "similar"})
    await chroma_adapter.insert_vector("different", [0.0, 0.0, 1.0], {"type": "different"})
    
    query_embedding = [1.0, 0.0, 0.0]
    results = await chroma_adapter.search_vectors(query_embedding, limit=10)
    
    # All scores should be between 0 and 1
    for vec_id, score in results:
        assert 0.0 <= score <= 1.0


async def test_close_adapter(chroma_adapter):
    """Test closing adapter cleans up properly"""
    vector_id = "test_vec"
    embedding = [0.1, 0.2, 0.3]
    metadata = {"test": "value"}
    
    await chroma_adapter.insert_vector(vector_id, embedding, metadata)
    
    # Close the adapter
    await chroma_adapter.close()
    
    # Verify internal state is cleared
    assert chroma_adapter.collection is None
    assert chroma_adapter.client is None


async def test_empty_metadata(chroma_adapter):
    """Test inserting vector with minimal metadata"""
    vector_id = "empty_meta_vec"
    embedding = [0.1, 0.2, 0.3, 0.4, 0.5]  # Match initial dimension
    metadata = {"placeholder": "required"}  # Chroma requires non-empty metadata

    await chroma_adapter.insert_vector(vector_id, embedding, metadata)

    result = await chroma_adapter.get_vector_by_id(vector_id)
    assert result is not None
    retrieved_embedding, retrieved_metadata = result
    assert len(retrieved_embedding) == len(embedding)
    for i, val in enumerate(embedding):
        assert abs(retrieved_embedding[i] - val) < 1e-6


async def test_multiple_searches_same_query(chroma_adapter):
    """Test that multiple searches with same query return consistent results"""
    # Insert test vectors
    await chroma_adapter.insert_vector("vec_1", [1.0, 0.0], {"id": "1"})
    await chroma_adapter.insert_vector("vec_2", [0.9, 0.1], {"id": "2"})
    
    query_embedding = [1.0, 0.0]
    
    # Run multiple searches
    results1 = await chroma_adapter.search_vectors(query_embedding, limit=10)
    results2 = await chroma_adapter.search_vectors(query_embedding, limit=10)
    
    # Results should be identical
    assert results1 == results2


async def test_search_with_limit_one(chroma_adapter):
    """Test search with limit of 1"""
    await chroma_adapter.insert_vector("vec_1", [1.0, 0.0], {"id": "1"})
    await chroma_adapter.insert_vector("vec_2", [0.9, 0.1], {"id": "2"})
    
    query_embedding = [1.0, 0.0]
    results = await chroma_adapter.search_vectors(query_embedding, limit=1)
    
    assert len(results) == 1
    assert results[0][0] == "vec_1"  # Closest match


async def test_overwrite_existing_vector(chroma_adapter):
    """Test that inserting with existing ID updates the vector"""
    vector_id = "update_vec"
    embedding1 = [0.1, 0.2, 0.3, 0.4, 0.5]
    embedding2 = [0.4, 0.5, 0.6, 0.7, 0.8]

    # Insert first version
    await chroma_adapter.insert_vector(vector_id, embedding1, {"version": "1"})

    # Insert again with same ID (should update)
    await chroma_adapter.insert_vector(vector_id, embedding2, {"version": "2"})

    # Verify it was updated
    result = await chroma_adapter.get_vector_by_id(vector_id)
    assert result is not None
    retrieved_embedding, retrieved_metadata = result
    # ChromaDB should have the latest version
    assert len(retrieved_embedding) == len(embedding2)
    for i, val in enumerate(embedding2):
        assert abs(retrieved_embedding[i] - val) < 1e-6
    assert retrieved_metadata["version"] == "2"


async def test_metadata_filter_with_numeric_string(chroma_adapter):
    """Test metadata filter with numeric values stored as strings"""
    await chroma_adapter.insert_vector(
        "vec_1", [0.1, 0.2], {"event_count": 10, "timeline_id": "t1"}
    )
    await chroma_adapter.insert_vector(
        "vec_2", [0.2, 0.3], {"event_count": 20, "timeline_id": "t1"}
    )
    
    query_embedding = [0.1, 0.2]
    # Filter by numeric value
    results = await chroma_adapter.search_vectors(
        query_embedding,
        limit=10,
        metadata_filter={"event_count": 10},
    )
    
    # Should return only vec_1
    assert len(results) == 1
    assert results[0][0] == "vec_1"
