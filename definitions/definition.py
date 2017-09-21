from backends.software_package import SoftwarePackage
from providers.provider import Provider


class SoftwareDefinition:
    """
    A software definition.

    It defines the name and vendor of the software product.
    A Provider (subclass) instance is specified as provider.
    The path_map specifies a (usual) mapping from web root path to the source
      code repository.
    """
    software_package: SoftwarePackage
    provider: Provider
    path_map: dict
