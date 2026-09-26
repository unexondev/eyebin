from typing import Hashable
from uuid import UUID, uuid4

class CacheManager:

    _entries : dict[UUID, Hashable] = {}
    _keys : dict[Hashable, UUID] = {}

    @staticmethod
    def create_id() -> UUID:
        return uuid4()

    @classmethod
    def cached(cls, id : UUID) -> bool:
        return id in cls._entries

    @classmethod
    def get(cls, id : UUID) -> Hashable | None:
        return cls._entries.get(id, None)

    @classmethod
    def cache(cls, entry : Hashable, id : UUID | None = None) -> UUID:
        id_cached = cls.find(entry)
        if id_cached is not None:
            return id_cached
        if id is None:
            id = cls.create_id()
        if id in cls._entries:
            raise ValueError("ID %s is already cached" % id)
        cls._entries[id] = entry
        cls._keys[entry] = id
        return id

    @classmethod
    def evict(cls, id : UUID):
        entry = cls._entries.pop(id)
        del cls._keys[entry]

    @classmethod
    def find(cls, entry : Hashable) -> UUID:
        return cls._keys.get(entry, None)

    @classmethod
    def has(cls, entry : Hashable) -> bool:
        return entry in cls._entries.values()