from collections import Callable

import attr
from cached_property import cached_property
from widgetastic.utils import VersionPick


@attr.s
class EntityCollections(object):
    """Caches instances of collection objects for use by the collections accessor
    The application object has a ``collections`` attribute. This attribute is an instance
    of this class. It is initialized with an application object and locally stores a cache
    of all known good collections.
    """

    _parent = attr.ib(repr=False, cmp=False, hash=False)
    _availiable_collections = attr.ib(repr=False, cmp=False, hash=False)
    _filters = attr.ib(cmp=False, hash=False, default=attr.Factory(dict))
    _collection_cache = attr.ib(
        repr=False, cmp=False, hash=False, init=False, default=attr.Factory(dict)
    )

    @classmethod
    def for_application(cls, application):
        from usmqe.web.application import load_application_collections
        return cls(
            parent=application, availiable_collections=load_application_collections()
        )

    @classmethod
    def for_entity(cls, entity, collections):
        return cls(
            parent=entity,
            availiable_collections=collections,
            filters={"parent": entity},
        )

    @classmethod
    def declared(cls, **spec):
        """returns a cached property named collections for use in entities"""

        @cached_property
        def collections(self):
            return cls.for_entity(self, spec)

        collections.spec = spec
        return collections

    def __dir__(self):
        internal_dir = dir(super(EntityCollections, self))
        return internal_dir + list(self._availiable_collections.keys())

    def __getattr__(self, name):
        if name not in self._availiable_collections:
            sorted_collection_keys = sorted(self._availiable_collections)
            raise AttributeError(
                "Collection [{}] not known to object, available collections: {}".format(
                    name, sorted_collection_keys
                )
            )
        if name not in self._collection_cache:
            item_filters = self._filters.copy()
            cls_and_or_filter = self._availiable_collections[name]
            if isinstance(cls_and_or_filter, tuple):
                item_filters.update(cls_and_or_filter[1])
                cls_or_verpick = cls_and_or_filter[0]
            else:
                cls_or_verpick = cls_and_or_filter
            # Now check whether we verpick the collection or not
            if isinstance(cls_or_verpick, VersionPick):
                cls = cls_or_verpick.pick(self._parent.application.version)
                try:
                    # TODO Add logger
                    print(
                        "[COLLECTIONS] Version picked collection %s as %s.%s",
                        name,
                        cls.__module__,
                        cls.__name__,
                    )
                except (AttributeError, TypeError, ValueError):
                    # TODO Add logger
                    print(
                        "[COLLECTIONS] Is the collection %s truly a collection?", name
                    )
            else:
                cls = cls_or_verpick
            self._collection_cache[name] = cls(self._parent, filters=item_filters)
        return self._collection_cache[name]


@attr.s
class BaseCollection(object):
    """Class for helping create consistent Collections
    The BaseCollection class is responsible for ensuring two things:
    1) That the API consistently has the first argument passed to it
    2) That that first argument is an application instance
    This class works in tandem with the entrypoint loader which ensures that the correct
    argument names have been used.
    """

    ENTITY = None

    parent = attr.ib(repr=False)
    filters = attr.ib(default=attr.Factory(dict))

    @property
    def application(self):
        if isinstance(self.parent, BaseEntity):
            return self.parent.application
        else:
            return self.parent

    @classmethod
    def for_application(cls, application, *k, **kw):
        return cls(application)

    @classmethod
    def for_entity(cls, obj, *k, **kw):
        return cls(obj, *k, **kw)

    @classmethod
    def for_entity_with_filter(cls, obj, filt, *k, **kw):
        return cls.for_entity(obj, *k, **kw).filter(filt)

    def instantiate(self, *args, **kwargs):
        return self.ENTITY.from_collection(self, *args, **kwargs)

    def filter(self, filter):
        filters = self.filters.copy()
        filters.update(filter)
        return attr.evolve(self, filters=filters)


@attr.s
class BaseEntity(object):
    """Class for helping create consistent entitys
    The BaseEntity class is responsible for ensuring two things:
    1) That the API consistently has the first argument passed to it
    2) That that first argument is a collection instance
    This class works in tandem with the entrypoint loader which ensures that the correct
    argument names have been used.
    """

    parent = attr.ib(repr=False)  # This is the collection or not

    @property
    def application(self):
        return self.parent.application

    @classmethod
    def from_collection(cls, collection, *k, **kw):
        return cls(collection, *k, **kw)

    @cached_property
    def collections(self):
        try:
            spec = self._collections
        except AttributeError:
            raise AttributeError("collections")

        return EntityCollections.for_entity(self, spec)


@attr.s
class CollectionProperty(object):
    type_or_get_type = attr.ib(validator=attr.validators.instance_of((Callable, type)))

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if not isinstance(self.type_or_get_type, type):
            self.type_or_get_type = self.type_or_get_type()
        return self.type_or_get_type.for_entity_with_filter(
            instance, {"parent": instance}
        )


def _walk_to_obj_root(obj):
    old = None
    while True:
        if old is obj:
            break
        yield obj
        old = obj
        try:
            obj = obj.parent
        except AttributeError:
            pass


def parent_of_type(obj, klass):
    for x in _walk_to_obj_root(obj):
        if isinstance(x, klass):
            return x
