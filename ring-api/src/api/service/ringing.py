from api.db import dynamo
from api.models.ringing import Ringing
from datetime import date
from api.utils import has_access


def get_ringing_by_ring(ring: str, user: str) -> Ringing | None:
    ringing = dynamo.get_ringing_by_ring(ring)
    assert has_access(user, ringing.id), "User does not have access to this ringing"
    return ringing


def delete_ringing(ring: str, user: str) -> None:
    """
    Delete a Ringing record from DynamoDB using its ring number.
    If the ring doesn't exist, the operation will still succeed.
    """
    assert has_access(user, ring), "User does not have access to this ringing"
    dynamo.delete_ringing(ring)


def upsert_ringing(ringing: Ringing, user: str) -> Ringing:
    """
    Insert or update a Ringing record in DynamoDB.
    The ring number serves as the primary key, so this will overwrite any existing record with the same ring.
    """
    assert has_access(user, ringing.ring), "User does not have access to this ringing"
    dynamo.put_ringing(ringing)
    return ringing


if __name__ == "__main__":
    ringing = Ringing(
        ring="123456",
        ring_scheme="PARIS",
        species="PARMAJ",
        date=date.today(),
        place="Some Location",
        lat=52.520008,
        lon=13.404954,
        ringer="John Doe",
        sex=1,
        age=2,
    )
    res = get_ringing_by_ring("123456")
    print("1")
    print(res)
    upsert_ringing(ringing)
    res = get_ringing_by_ring("123456")
    print("2")
    print(res)
    ringing.age = 3
    upsert_ringing(ringing)
    res = get_ringing_by_ring("123456")
    print("3")
    print(res)
    delete_ringing("123456")
