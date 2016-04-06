import inspect
import operator
import re

from django.http import HttpResponse


class Action:

    def __init__(self, identifier, method, doc=None):
        self.identifier = identifier
        if doc is not None:
            self.doc = doc.strip()
        else:
            self.doc = ""
        self.method = method


class Resource:

    def __init__(self, name, url, doc=None):
        self.name = name
        self.url = url
        if doc is not None:
            self.doc = doc.strip()
        else:
            self.doc = ""
        self.actions = []


class ResourceGroup:

    def __init__(self, name, doc=None):
        self.name = name.strip()
        if doc is not None:
            self.doc = doc.strip()
        else:
            self.doc = ""
        self.resources = []


def format_url(url):
    url_re = re.compile(url)
    rurl2 = []
    bits = re.split(r"(\([^\)]*\))", url_re.pattern)
    i = 0
    a = sorted(url_re.groupindex.items(), key=operator.itemgetter(1))
    for bit in bits:
        if bit.startswith("(") and bit.endswith(")"):
            key = "id" if a[i][0] == "pk" else a[i][0]
            rurl2.append("{{{}}}".format(key))
        else:
            rurl2.append(bit)
    return "".join(rurl2)


def viewset_actions(viewset, **kwargs):
    for method, attr in viewset.view_mapping(**kwargs).items():
        view = getattr(viewset, attr, None)
        if view is not None:
            doc = trim(view.__doc__).splitlines()
            if doc[0].startswith("Identifier: "):
                identifier = doc[0][12:]
                doc = doc[1:]
            else:
                identifier = "Unknown action"
            yield Action(identifier, method.upper(), doc="\n".join(doc))


class DocumentationGenerator:

    @classmethod
    def from_api(cls, api):
        resource_groups = []
        for viewset in api:
            resource_group = ResourceGroup(viewset.docs["verbose_name_plural"], viewset.__doc__)
            # list resource
            resource = Resource(
                name=viewset.docs["verbose_name_plural"],
                url=format_url(viewset.url.collection_regex()),
            )
            resource.actions.extend(list(viewset_actions(viewset, collection=True)))
            resource_group.resources.append(resource)
            # detail resource
            resource = Resource(
                name=viewset.docs["verbose_name"],
                url=format_url(viewset.url.detail_regex()),
            )
            resource.actions.extend(list(viewset_actions(viewset, collection=False)))
            resource_group.resources.append(resource)
            # relationship resources
            for related_name, rel_viewset in viewset.relationships.items():
                resource = Resource(
                    name=viewset.docs["verbose_name_plural"],
                    url=format_url("{}/relationships/{}".format(viewset.url.detail_regex(), related_name)),
                )
                resource.actions.extend(list(viewset_actions(rel_viewset)))
                resource_group.resources.append(resource)
            # wrap up
            resource_groups.append(resource_group)
        return cls(api.name, trim(api.__doc__), api.host, resource_groups)

    def __init__(self, name, description, host, resource_groups):
        self.name = name
        self.description = description
        self.host = host
        self.resource_groups = resource_groups

    def render(self):
        lines = ["FORMAT: 1A"]
        if self.host:
            lines.append("HOST: {}".format(self.host))
        lines.extend([
            "",
            "# {}".format(self.name),
            "",
        ])
        if self.description:
            lines.extend(self.description.splitlines())
        for resource_group in self.resource_groups:
            lines.append("")
            lines.append("# Group {}".format(resource_group.name))
            if resource_group.doc:
                lines.append("")
                lines.extend(trim(resource_group.doc).splitlines())
            for resource in resource_group.resources:
                lines.append("")
                lines.append("## {} [/{}]".format(resource.name, resource.url))
                if resource.doc:
                    lines.append("")
                    lines.extend(trim(resource.doc).splitlines())
                for action in resource.actions:
                    lines.append("")
                    lines.append("### {} [{}]".format(action.identifier, action.method))
                    if action.doc:
                        lines.append("")
                        lines.extend(action.doc.splitlines())
        return "\n".join(lines)


def trim(docstring):
    return inspect.cleandoc(docstring)


def doc_view(api):
    def view(request):
        a = api()
        a.host = "{}://{}".format(request.scheme, request.get_host())
        dg = DocumentationGenerator.from_api(a)
        response = HttpResponse(dg.render())
        response["Content-Type"] = "text/vnd.apiblueprint"
        return response
    return view
