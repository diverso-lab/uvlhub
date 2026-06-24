"""Serialisers that expose dataset metadata under FAIR-friendly shapes.

Emitted representations:
    * schema.org Dataset JSON-LD (embedded and content-negotiated)
    * Dublin Core / DCTERMS HTML meta tags
    * Datacite JSON
    * Turtle (hand-serialised, no rdflib dependency)
"""

from __future__ import annotations

from urllib.parse import quote

CC_BY_40 = "https://creativecommons.org/licenses/by/4.0/"
CC_BY_40_NAME = "Creative Commons Attribution 4.0 International"
UVL_SPEC = "https://universal-variability-language.github.io/"
UVLHUB_URL = "https://www.uvlhub.io"
UVLHUB_ORG = {
    "@type": "Organization",
    "name": "uvlhub",
    "url": UVLHUB_URL,
}
UVLHUB_CATALOG = {
    "@type": "DataCatalog",
    "name": "uvlhub",
    "url": UVLHUB_URL,
}
UVL_MEDIA_TYPE = "text/plain"


def _doi_url(doi):
    if not doi:
        return None
    return doi if doi.startswith("http") else f"https://doi.org/{doi}"


def _zenodo_url(deposition_id):
    return f"https://zenodo.org/record/{deposition_id}" if deposition_id else None


def _keywords(dataset):
    tags = dataset.ds_meta_data.tags
    if not tags:
        return []
    return [t.strip() for t in tags.split(",") if t.strip()]


def _landing_url(dataset, host_url):
    doi = dataset.ds_meta_data.dataset_doi
    if not doi:
        return host_url.rstrip("/")
    return f"{host_url.rstrip('/')}/doi/{doi}/"


def _distributions(dataset, host_url):
    base = host_url.rstrip("/")
    doi = dataset.ds_meta_data.dataset_doi or ""
    out = []
    for fm in dataset.feature_models:
        for f in fm.hubfiles:
            out.append(
                {
                    "name": f.name,
                    "url": f"{base}/doi/{doi}/files/raw/{quote(f.name, safe='')}",
                    "size": int(f.size) if f.size is not None else 0,
                }
            )
    return out


def _orcid_url(raw):
    if not raw:
        return None
    return raw if raw.startswith("http") else f"https://orcid.org/{raw}"


def _authors_jsonld(dataset):
    out = []
    for a in dataset.ds_meta_data.authors:
        person = {"@type": "Person", "name": a.name}
        if a.affiliation:
            person["affiliation"] = {"@type": "Organization", "name": a.affiliation}
        orcid = _orcid_url(a.orcid)
        if orcid:
            person["@id"] = orcid
            person["identifier"] = {
                "@type": "PropertyValue",
                "propertyID": "ORCID",
                "value": a.orcid,
                "url": orcid,
            }
        out.append(person)
    return out


def _date(dataset):
    return dataset.created_at.strftime("%Y-%m-%d") if dataset.created_at else None


def _year(dataset):
    return dataset.created_at.year if dataset.created_at else None


def build_json_ld(dataset, host_url):
    meta = dataset.ds_meta_data
    doi = meta.dataset_doi
    doi_url = _doi_url(doi)
    landing = _landing_url(dataset, host_url)
    zenodo = _zenodo_url(meta.deposition_id)

    identifiers = []
    if doi:
        identifiers.append(
            {
                "@type": "PropertyValue",
                "propertyID": "DOI",
                "value": doi,
                "url": doi_url,
            }
        )
    if zenodo:
        identifiers.append(
            {
                "@type": "PropertyValue",
                "propertyID": "Zenodo",
                "value": str(meta.deposition_id),
                "url": zenodo,
            }
        )

    distributions = [
        {
            "@type": "DataDownload",
            "name": d["name"],
            "encodingFormat": UVL_MEDIA_TYPE,
            "contentUrl": d["url"],
            "contentSize": str(d["size"]),
        }
        for d in _distributions(dataset, host_url)
    ]

    same_as = [u for u in (doi_url, zenodo) if u]

    doc = {
        "@context": {
            "@vocab": "https://schema.org/",
            "schema": "https://schema.org/",
            "dcterms": "http://purl.org/dc/terms/",
            "foaf": "http://xmlns.com/foaf/0.1/",
        },
        "@type": "Dataset",
        "@id": doi_url or landing,
        "url": landing,
        "identifier": identifiers,
        "name": meta.title,
        "description": meta.description,
        "creator": _authors_jsonld(dataset),
        "publisher": UVLHUB_ORG,
        "provider": UVLHUB_ORG,
        "datePublished": _date(dataset),
        "dateCreated": _date(dataset),
        "dateModified": _date(dataset),
        "inLanguage": "en",
        "keywords": _keywords(dataset),
        "license": CC_BY_40,
        "isAccessibleForFree": True,
        "conditionsOfAccess": "Open Access",
        "accessMode": "textual",
        "accessModeSufficient": ["textual"],
        "version": "1.0",
        "encodingFormat": UVL_MEDIA_TYPE,
        "sameAs": same_as,
        "includedInDataCatalog": UVLHUB_CATALOG,
        "distribution": distributions,
        "conformsTo": UVL_SPEC,
        "dcterms:conformsTo": {"@id": UVL_SPEC},
        "dcterms:license": {"@id": CC_BY_40},
        "dcterms:type": "http://purl.org/dc/dcmitype/Dataset",
    }
    if meta.publication_doi:
        doc["citation"] = _doi_url(meta.publication_doi)
        doc["isBasedOn"] = _doi_url(meta.publication_doi)
    return {k: v for k, v in doc.items() if v not in (None, [], "")}


def build_dublin_core_tags(dataset):
    """Returns (name, content) pairs to be emitted as <meta> tags."""
    meta = dataset.ds_meta_data
    doi = meta.dataset_doi
    doi_url = _doi_url(doi)
    date = _date(dataset)
    pairs = []
    base = [
        ("DC.title", meta.title),
        ("DCTERMS.title", meta.title),
        ("DC.description", meta.description),
        ("DCTERMS.description", meta.description),
        ("DC.publisher", "uvlhub"),
        ("DCTERMS.publisher", "uvlhub"),
        ("DC.type", "Dataset"),
        ("DCTERMS.type", "http://purl.org/dc/dcmitype/Dataset"),
        ("DC.format", UVL_MEDIA_TYPE),
        ("DCTERMS.format", UVL_MEDIA_TYPE),
        ("DC.language", "en"),
        ("DCTERMS.language", "en"),
        ("DC.rights", CC_BY_40_NAME),
        ("DCTERMS.rights", CC_BY_40_NAME),
        ("DCTERMS.license", CC_BY_40),
        ("DCTERMS.accessRights", "Open Access"),
        ("DC.date", date),
        ("DCTERMS.issued", date),
        ("DCTERMS.created", date),
        ("DCTERMS.modified", date),
    ]
    if doi:
        base.append(("DC.identifier", f"doi:{doi}"))
        base.append(("DCTERMS.identifier", f"doi:{doi}"))
        base.append(("DC.identifier.URI", doi_url))
    if meta.deposition_id:
        base.append(("DC.source", _zenodo_url(meta.deposition_id)))
        base.append(("DCTERMS.source", _zenodo_url(meta.deposition_id)))
    if meta.publication_doi:
        base.append(("DCTERMS.isReferencedBy", _doi_url(meta.publication_doi)))
    base.append(("DCTERMS.conformsTo", UVL_SPEC))
    for name, content in base:
        if content:
            pairs.append((name, content))
    for author in meta.authors:
        pairs.append(("DC.creator", author.name))
        pairs.append(("DCTERMS.creator", author.name))
        orcid = _orcid_url(author.orcid)
        if orcid:
            pairs.append(("DCTERMS.creator.ORCID", orcid))
    for kw in _keywords(dataset):
        pairs.append(("DC.subject", kw))
        pairs.append(("DCTERMS.subject", kw))
    if doi:
        pairs.append(("citation_doi", doi))
    pairs.append(("citation_title", meta.title))
    if date:
        pairs.append(("citation_publication_date", date.replace("-", "/")))
    for author in meta.authors:
        pairs.append(("citation_author", author.name))
    pairs.append(("citation_publisher", "uvlhub"))
    pairs.append(("citation_language", "en"))
    return pairs


def build_datacite_json(dataset):
    meta = dataset.ds_meta_data
    creators = []
    for a in meta.authors:
        c = {"name": a.name, "nameType": "Personal"}
        if a.affiliation:
            c["affiliation"] = [{"name": a.affiliation}]
        orcid = _orcid_url(a.orcid)
        if orcid:
            c["nameIdentifiers"] = [
                {
                    "nameIdentifier": orcid,
                    "nameIdentifierScheme": "ORCID",
                    "schemeUri": "https://orcid.org",
                }
            ]
        creators.append(c)
    attrs = {
        "doi": meta.dataset_doi,
        "url": _doi_url(meta.dataset_doi),
        "titles": [{"title": meta.title, "lang": "en"}],
        "creators": creators,
        "publisher": "uvlhub",
        "publicationYear": _year(dataset),
        "types": {
            "resourceType": "Dataset",
            "resourceTypeGeneral": "Dataset",
            "schemaOrg": "Dataset",
        },
        "descriptions": [
            {
                "description": meta.description,
                "descriptionType": "Abstract",
                "lang": "en",
            }
        ],
        "subjects": [{"subject": k, "lang": "en"} for k in _keywords(dataset)],
        "rightsList": [
            {
                "rights": CC_BY_40_NAME,
                "rightsUri": CC_BY_40,
                "rightsIdentifier": "cc-by-4.0",
                "rightsIdentifierScheme": "SPDX",
                "schemeUri": "https://spdx.org/licenses/",
            }
        ],
        "language": "en",
        "formats": [UVL_MEDIA_TYPE],
        "version": "1.0",
        "dates": [{"date": _date(dataset), "dateType": "Issued"}] if _date(dataset) else [],
    }
    relations = []
    if meta.deposition_id:
        relations.append(
            {
                "relatedIdentifier": str(meta.deposition_id),
                "relatedIdentifierType": "URL",
                "relationType": "IsIdenticalTo",
            }
        )
    if meta.publication_doi:
        relations.append(
            {
                "relatedIdentifier": meta.publication_doi,
                "relatedIdentifierType": "DOI",
                "relationType": "IsSupplementTo",
            }
        )
    if relations:
        attrs["relatedIdentifiers"] = relations
    return {"data": {"type": "dois", "id": meta.dataset_doi or "", "attributes": attrs}}


def build_turtle(dataset, host_url):
    """Minimal Turtle serialisation. No rdflib required."""
    meta = dataset.ds_meta_data
    doi_url = _doi_url(meta.dataset_doi)
    landing = _landing_url(dataset, host_url)
    subject_iri = doi_url or landing
    zenodo = _zenodo_url(meta.deposition_id)
    date = _date(dataset)

    def esc(s):
        return str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")

    lines = [
        "@prefix schema: <https://schema.org/> .",
        "@prefix dcterms: <http://purl.org/dc/terms/> .",
        "@prefix dcat: <http://www.w3.org/ns/dcat#> .",
        "@prefix foaf: <http://xmlns.com/foaf/0.1/> .",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        "",
        f"<{subject_iri}> a schema:Dataset , dcat:Dataset ;",
        f'    schema:name "{esc(meta.title)}" ;',
        f'    dcterms:title "{esc(meta.title)}" ;',
        f'    schema:description "{esc(meta.description)}" ;',
        f'    dcterms:description "{esc(meta.description)}" ;',
        f"    schema:url <{landing}> ;",
        f'    schema:publisher [ a schema:Organization ; schema:name "uvlhub" ; schema:url <{UVLHUB_URL}> ] ;',
        '    dcterms:publisher "uvlhub" ;',
        f"    schema:license <{CC_BY_40}> ;",
        f"    dcterms:license <{CC_BY_40}> ;",
        f'    dcterms:rights "{CC_BY_40_NAME}" ;',
        '    dcterms:accessRights "Open Access" ;',
        "    schema:isAccessibleForFree true ;",
        '    schema:conditionsOfAccess "Open Access" ;',
        '    schema:inLanguage "en" ;',
        '    dcterms:language "en" ;',
        f'    schema:encodingFormat "{UVL_MEDIA_TYPE}" ;',
        f'    dcterms:format "{UVL_MEDIA_TYPE}" ;',
        "    dcterms:type <http://purl.org/dc/dcmitype/Dataset> ;",
        f"    schema:conformsTo <{UVL_SPEC}> ;",
        f"    dcterms:conformsTo <{UVL_SPEC}> ;",
        '    schema:version "1.0" ;',
        f'    dcterms:identifier "{esc(meta.dataset_doi or "")}" ;',
    ]
    if date:
        lines.append(f'    schema:datePublished "{date}"^^xsd:date ;')
        lines.append(f'    dcterms:issued "{date}"^^xsd:date ;')
        lines.append(f'    schema:dateCreated "{date}"^^xsd:date ;')
        lines.append(f'    dcterms:created "{date}"^^xsd:date ;')
        lines.append(f'    dcterms:modified "{date}"^^xsd:date ;')
    for kw in _keywords(dataset):
        lines.append(f'    schema:keywords "{esc(kw)}" ;')
        lines.append(f'    dcterms:subject "{esc(kw)}" ;')
    for a in meta.authors:
        orcid = _orcid_url(a.orcid)
        if orcid:
            lines.append(f"    schema:creator <{orcid}> ;")
            lines.append(f"    dcterms:creator <{orcid}> ;")
        else:
            lines.append(f'    schema:creator [ a schema:Person ; schema:name "{esc(a.name)}" ] ;')
            lines.append(f'    dcterms:creator "{esc(a.name)}" ;')
    if zenodo:
        lines.append(f"    schema:sameAs <{zenodo}> ;")
        lines.append(f"    dcterms:isVersionOf <{zenodo}> ;")
    if meta.publication_doi:
        pub_url = _doi_url(meta.publication_doi)
        lines.append(f"    schema:citation <{pub_url}> ;")
        lines.append(f"    dcterms:isReferencedBy <{pub_url}> ;")
    lines.append(
        "    schema:includedInDataCatalog [ a schema:DataCatalog ; "
        f'schema:name "uvlhub" ; schema:url <{UVLHUB_URL}> ] ;'
    )

    dists = _distributions(dataset, host_url)
    if dists:
        dist_iris = " , ".join(f"<{d['url']}>" for d in dists)
        lines.append(f"    schema:distribution {dist_iris} ;")
        lines.append(f"    dcat:distribution {dist_iris} .")
        for d in dists:
            lines.append("")
            lines.append(f"<{d['url']}> a schema:DataDownload , dcat:Distribution ;")
            lines.append(f'    schema:encodingFormat "{UVL_MEDIA_TYPE}" ;')
            lines.append(f'    dcat:mediaType "{UVL_MEDIA_TYPE}" ;')
            lines.append(f'    schema:contentSize "{d["size"]}"^^xsd:integer ;')
            lines.append(f'    dcat:byteSize "{d["size"]}"^^xsd:integer ;')
            lines.append(f'    schema:contentUrl <{d["url"]}> ;')
            lines.append(f'    dcat:downloadURL <{d["url"]}> ;')
            lines.append(f'    schema:name "{esc(d["name"])}" .')
    else:
        lines[-1] = lines[-1].rstrip(" ;") + " ."
    return "\n".join(lines) + "\n"


def build_link_header(dataset, host_url):
    """RFC 9264 signposting Link header value."""
    meta = dataset.ds_meta_data
    doi_url = _doi_url(meta.dataset_doi)
    landing = _landing_url(dataset, host_url)
    parts = []
    if doi_url:
        parts.append(f'<{doi_url}>; rel="cite-as"')
    parts.append(f'<{landing}>; rel="describedby"; type="application/ld+json"')
    parts.append(f'<{landing}>; rel="describedby"; type="text/turtle"')
    parts.append(f'<{landing}>; rel="describedby"; type="application/vnd.datacite.datacite+json"')
    parts.append(f'<{CC_BY_40}>; rel="license"')
    parts.append('<https://schema.org/Dataset>; rel="type"')
    parts.append('<http://purl.org/dc/dcmitype/Dataset>; rel="type"')
    for author in meta.authors:
        orcid = _orcid_url(author.orcid)
        if orcid:
            parts.append(f'<{orcid}>; rel="author"')
    if meta.publication_doi:
        pub_url = _doi_url(meta.publication_doi)
        parts.append(f'<{pub_url}>; rel="cite-as"')
    return ", ".join(parts)
