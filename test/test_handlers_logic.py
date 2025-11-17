import pytest
import asyncio

from logic.rating_manager import add_rating, get_stats, should_delete

@pytest.mark.asyncio
async def test_simulated_vote_flow():
    msg_id = 777

    # Simuliamo 3 utenti che votano
    await add_rating(msg_id, 10, 3)
    await add_rating(msg_id, 11, 4)
    await add_rating(msg_id, 12, 5)

    count, avg = await get_stats(msg_id)

    assert count == 3
    assert avg == pytest.approx(4.0)
    assert await should_delete(msg_id) is False
