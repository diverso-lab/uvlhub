import re

import unidecode

from flask import render_template, request, abort, jsonify
from sqlalchemy import or_, desc, asc, any_

from . import explore_bp
from .forms import ExploreForm
from ..dataset.models import DataSet, DSMetaData, Author, FeatureModel, FMMetaData, PublicationType


@explore_bp.route('/explore', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        query = request.args.get('query', '')
        form = ExploreForm()
        return render_template('explore/index.html', form=form, query=query)
    elif request.method == 'POST':
        criteria = request.get_json()
        query = criteria.get('query', '')
        order = criteria.get('sorting', 'newest')
        publication_type = criteria.get('publication_type', 'any')
        tags = criteria.get('tags', [])

        # Normalize and remove unwanted characters
        normalized_query = unidecode.unidecode(query).lower()
        cleaned_query = re.sub(r'[,.":\'()\[\]^;!¡¿?]', '', normalized_query)
        query_words = cleaned_query.split()

        filters = []
        for word in query_words:
            filters.append(DSMetaData.title.ilike(f'%{word}%'))
            filters.append(DSMetaData.description.ilike(f'%{word}%'))
            filters.append(Author.name.ilike(f'%{word}%'))
            filters.append(Author.affiliation.ilike(f'%{word}%'))
            filters.append(Author.orcid.ilike(f'%{word}%'))
            filters.append(FMMetaData.uvl_filename.ilike(f'%{word}%'))
            filters.append(FMMetaData.title.ilike(f'%{word}%'))
            filters.append(FMMetaData.description.ilike(f'%{word}%'))
            filters.append(FMMetaData.publication_type.ilike(f'%{word}%'))
            filters.append(FMMetaData.publication_doi.ilike(f'%{word}%'))
            filters.append(FMMetaData.tags.ilike(f'%{word}%'))
            filters.append(DSMetaData.tags.ilike(f'%{word}%'))

        datasets = DataSet.query \
            .join(DSMetaData) \
            .join(Author) \
            .join(FeatureModel) \
            .join(FMMetaData)

        if publication_type != 'any':
            matching_type = None
            for member in PublicationType:
                if member.value.lower() == publication_type:
                    matching_type = member
                    break

            if matching_type is not None:
                datasets = datasets.filter(DSMetaData.publication_type == matching_type.name)

        datasets = datasets.filter(or_(*filters))

        if tags:
            datasets = datasets.filter(DSMetaData.tags.ilike(any_(f'%{tag}%' for tag in tags)))

        # Order by created_at
        if order == 'oldest':
            datasets = datasets.order_by(DataSet.created_at.asc())
        else:
            datasets = datasets.order_by(DataSet.created_at.desc())

        datasets = datasets.all()

        dataset_dicts = [dataset.to_dict() for dataset in datasets]

        return jsonify(dataset_dicts)
