import re

pattern = re.compile(
    r"(?P<propertyName>(?=^)\w[\s\w,]+)"
    r"(?(1):)(?:\s|\n)?(?P<propertyData>[\W\w\s]+)",
    re.MULTILINE,
)

f_pattern = re.compile(r"(?P<propertyName>(?=^)\w[\s\w,]+)(?(1):)", re.MULTILINE)
