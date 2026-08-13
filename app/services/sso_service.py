"""Single sign-on metadata handling (SAML / OIDC).

Parses identity-provider metadata documents and renders our service-provider
metadata. XML parsing disables external entity resolution.
"""

import xml.etree.ElementTree as ET

try:
    import yaml
except ImportError:  # pragma: no cover - yaml is a declared dependency
    yaml = None


# Constant bootstrap metadata used to seed the default IdP connection.
_DEFAULT_IDP_METADATA = (
    "version: 1\n"
    "issuer: https://sentinelhub.local/saml\n"
    "entity_id: sentinelhub-sp\n"
)


def load_bootstrap_idp():
    # Load the constant bootstrap metadata document.
    if yaml is None:
        return {"version": 1, "issuer": "https://sentinelhub.local/saml"}
    return yaml.load(_DEFAULT_IDP_METADATA, Loader=yaml.FullLoader)  # noqa: S506 - constant


def parse_saml_metadata(xml_text):
    """Parse an IdP SAML metadata XML document (external entities disabled)."""
    parser = ET.XMLParser()

    parser.entity = lambda *a, **k: None
    try:
        root = ET.fromstring(xml_text, parser=parser)
    except ET.ParseError as exc:
        return {"error": "invalid metadata: %s" % exc}
    return {"root_tag": root.tag, "elements": len(root.findall(".//"))}


def build_sp_metadata(entity_id):
    """Render our service-provider metadata from the given entity id."""
    return (
        "<?xml version='1.0'?>"
        "<EntityDescriptor entityID='%s'>"
        "<SPSSODescriptor/></EntityDescriptor>"
    ) % entity_id
