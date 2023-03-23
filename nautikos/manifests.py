import abc
from typing import TextIO, TypedDict

from .yaml import yaml


class Image(TypedDict):
    repository: str
    tag: str


class AbstractManifest(abc.ABC):
    def load(self, stream: TextIO) -> None:
        self._data = yaml.load(stream)

    def write(self, stream: TextIO) -> None:
        yaml.dump(self.data, stream)

    @property
    def data(self) -> str:
        if self._data:
            return self._data
        else:
            raise Exception("You must first load a manifest")

    @abc.abstractmethod
    def modify(self, repository: str, new_tag: str) -> str:
        ...

    @abc.abstractmethod
    def get_images(self) -> list[Image]:
        ...


KubernetesImageDefinition = str


class KubernetesContainer(TypedDict):
    image: KubernetesImageDefinition


class KubernetesManifest(AbstractManifest):
    def modify(self, repository: str, new_tag: str) -> None:
        for container in self._get_containers():
            if repository == self._parse_image(container["image"])["repository"]:
                container["image"] = self._unparse_image(
                    {"repository": repository, "tag": new_tag}
                )

    def get_images(self) -> list[Image]:
        return [
            self._parse_image(container["image"])
            for container in self._get_containers()
        ]

    def _get_containers(self) -> list[KubernetesContainer]:
        return self.data["spec"]["template"]["spec"]["containers"]

    def _parse_image(self, image: KubernetesImageDefinition) -> Image:
        if ":" in image:
            repository, tag = tuple(image.split(":"))
        else:
            repository, tag = image, None
        return {"repository": repository, "tag": tag}

    def _unparse_image(self, image: Image) -> str:
        return f"{image['repository']}:{image['tag']}"


class KustomizeImageDefinition(TypedDict):
    name: str
    newTag: str


class KustomizeManifest(AbstractManifest):
    def modify(self, repository: str, new_tag: str) -> None:
        for kustomize_image in self._data["images"]:
            if repository == kustomize_image["name"]:
                kustomize_image["newTag"] = new_tag

    def get_images(self) -> list[Image]:
        return [self._parse_image(image) for image in self._data["images"]]

    def _parse_image(self, image: KustomizeImageDefinition) -> Image:
        return {"repository": image["name"], "tag": image["newTag"]}


def get_manifest(type: str) -> AbstractManifest:
    if type == "kubernetes":
        manifest = KubernetesManifest()
    elif type == "kustomize":
        manifest = KustomizeManifest()
    elif type == "helm":
        raise Exception("Helm manifests are not yet implemented.")
    else:
        raise Exception(f"'{type}' is not a correct manifest type.")
    return manifest
