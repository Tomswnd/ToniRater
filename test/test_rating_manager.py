import pytest
import asyncio
from logic.old_rating_manager import add_rating, get_stats, should_delete
import json
import os

# Usa un file di test temporaneo
TEST_FILE = "data/ratings_test.json"

@pytest.fixture(autouse=True)
def cleanup():
    # Reset file prima di ogni test
    with open(TEST_FILE, "w") as f:
        json.dump({}, f)

    # Patch rating_manager per usare il file di test
    import logic.old_rating_manager as rm
    rm.RATINGS_FILE = TEST_FILE

    yield

    # Cleanup dopo test
    os.remove(TEST_FILE)


@pytest.mark.asyncio
async def test_add_and_get_stats():
    msg_id = 100

    await add_rating(msg_id, 1, 5)
    await add_rating(msg_id, 2, 3)
    await add_rating(msg_id, 3, 1)

    count, avg = await get_stats(msg_id)

    assert count == 3
    assert avg == pytest.approx((5 + 3 + 1) / 3)


@pytest.mark.asyncio
async def test_should_delete():
    msg_id = 200

    # Media = (1 + 2 + 2) / 3 = 1.66
    await add_rating(msg_id, 1, 1)
    await add_rating(msg_id, 2, 2)
    await add_rating(msg_id, 3, 2)

    decision = await should_delete(msg_id)
    assert decision is True


@pytest.mark.asyncio
async def test_should_not_delete_with_few_votes():
    msg_id = 300

    await add_rating(msg_id, 1, 1)
    await add_rating(msg_id, 2, 1)

    decision = await should_delete(msg_id)
    assert decision is False
