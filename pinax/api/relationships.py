
class Relationship:

    def __init__(self, collection=False, attributes=None, relationships=None):
        self.collection = collection
        self.attributes = attributes
        self.relationships = relationships

    def __call__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        return self
