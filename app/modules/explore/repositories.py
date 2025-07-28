import re
from sqlalchemy import any_, or_
import unidecode
from app.modules.dataset.models import Author, DSMetaData, DataSet, PublicationType
from app.modules.featuremodel.models import FeatureModel
from core.repositories.BaseRepository import BaseRepository


class ExploreRepository(BaseRepository):
    def __init__(self):
        super().__init__(DataSet)

    def filter(
        self, query="", sorting="newest", publication_type="any", tags=[], **kwargs
    ):
        # Normalize and clean query
        normalized_query = unidecode.unidecode(query).lower()
        cleaned_query = re.sub(r'[,.":\'()\[\]^;!¡¿?]', "", normalized_query)

        filters = []
        for word in cleaned_query.split():
            filters.append(DSMetaData.title.ilike(f"%{word}%"))
            filters.append(DSMetaData.description.ilike(f"%{word}%"))
            filters.append(Author.name.ilike(f"%{word}%"))
            filters.append(Author.affiliation.ilike(f"%{word}%"))
            filters.append(Author.orcid.ilike(f"%{word}%"))
            filters.append(DSMetaData.tags.ilike(f"%{word}%"))

        # Base query
        datasets = (
            self.model.query.join(DataSet.ds_meta_data)
            .join(DSMetaData.authors)
            .filter(or_(*filters))
            .filter(DSMetaData.dataset_doi.isnot(None))
        )

        if publication_type != "any":
            matching_type = None
            for member in PublicationType:
                if member.value.lower() == publication_type:
                    matching_type = member
                    break

            if matching_type is not None:
                datasets = datasets.filter(
                    DSMetaData.publication_type == matching_type
                )

        if tags:
            datasets = datasets.filter(
                DSMetaData.tags.ilike(any_(f"%{tag}%" for tag in tags))
            )

        if sorting == "oldest":
            datasets = datasets.order_by(self.model.created_at.asc())
        else:
            datasets = datasets.order_by(self.model.created_at.desc())

        return datasets.all()
