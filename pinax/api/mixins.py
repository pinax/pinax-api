
class DjangoModelEndpointSetMixin(object):

    def get_pk(self):
        """
        Convenience method returning URL PK kwarg.
        """
        pk_url_kwarg = self.url.lookup["field"]
        return self.kwargs[pk_url_kwarg] if pk_url_kwarg in self.kwargs else None

    def get_resource_object_model(self):
        """
        Convenience method returning Resource's object model, if any.
        """
        if hasattr(self, "resource_class"):
            return self.resource_class.model if hasattr(self.resource_class, "model") else None
        else:
            return None

    def get_queryset(self):
        """
        Convenience method returning all Resource's object model objects.
        """
        return self.get_resource_object_model()._default_manager.all()

    def prepare(self):
        """
        Sets `self.pk` to the requested PK
        Sets `self.obj` to a retrieved Resource object.

        Assumes Resource object is based on Django model.
        No action is taken if requested method does not operate on single objects.
        """
        if self.get_resource_object_model():
            if self.requested_method in ["retrieve", "update", "destroy"]:
                self.pk = self.get_pk()
                self.obj = self.get_object_or_404(self.get_queryset(), pk=self.pk)
