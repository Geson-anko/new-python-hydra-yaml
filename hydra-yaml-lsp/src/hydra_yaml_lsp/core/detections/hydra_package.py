import re
from dataclasses import dataclass

AT_PACKAGE = "@package"
HYDRA_PACKAGE_PATTERN = re.compile(rf"^#\s+{AT_PACKAGE}\s+([\w\.]+)")


@dataclass
class PackageName:
    """Information about a package name and its position.

    Attributes:
        content: The package name string.
        start: Starting position of the package name in the text.
        end: Ending position of the package name in the text.
    """

    content: str
    start: int
    end: int


@dataclass
class PackageDirective:
    start: int
    end: int
    content = AT_PACKAGE


@dataclass(frozen=True)
class HydraPackagePosition:
    """Complete position information for a Hydra package declaration.

    Attributes:
        name: Object containing the package name content and position.
        at_package_start: Starting position of the '@package' keyword.
        at_package_end: Ending position of the '@package' keyword.
        content: Complete text content of the package declaration line.
    """

    name: PackageName
    directive: PackageDirective
    content: str


def detect_hydra_package(content: str) -> HydraPackagePosition | None:
    """Detect a Hydra package declaration from the first line of text.

    Looks for a line starting with '# @package' followed by a valid package name.
    Package names can include dots to indicate hierarchical namespaces.

    Args:
        content: String to search for a Hydra package declaration.

    Returns:
        HydraPackagePosition object if a valid package declaration is found,
        None otherwise.

    Examples:
        >>> content = "# @package foo.bar\\nkey: value"
        >>> position = detect_hydra_package(content)
        >>> position.package_name.content
        'foo.bar'
    """
    if not content:
        return None

    line = content.split("\n", 1)[0]
    match = HYDRA_PACKAGE_PATTERN.match(line)
    if not match:
        return None

    at_package_start = line.find(AT_PACKAGE)
    at_package_end = at_package_start + len(AT_PACKAGE)

    # Extract package name from the regex capture group
    package_name = match.group(1)
    package_name_start = line.find(package_name, at_package_end)
    package_name_end = package_name_start + len(package_name)

    return HydraPackagePosition(
        PackageName(package_name, package_name_start, package_name_end),
        PackageDirective(at_package_start, at_package_end),
        line,
    )
