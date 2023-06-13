import re

import unidecode

from flask import render_template, request, abort, jsonify
from sqlalchemy import or_, desc, asc

from . import explore_bp
from .forms import ExploreForm
from ..dataset.models import DataSet, DSMetaData, Author, FeatureModel, FMMetaData, PublicationType


@explore_bp.route('/explore', methods=['GET'])
def index():
    form = ExploreForm()
    return render_template('explore/index.html', form=form)


@explore_bp.route('/explore', methods=['POST'])
def explore():
    criteria = request.get_json()
    query = criteria.get('query', '')
    order = criteria.get('sorting', 'newest')
    publication_type = criteria.get('publication_type', 'any')

    # Normalize and remove unwanted characters
    normalized_query = unidecode.unidecode(query).lower()
    cleaned_query = re.sub(r'[,.]', '', normalized_query)
    query_words = cleaned_query.split()

    filters = []
    for word in query_words:
        filters.append(DSMetaData.title.ilike(f'%{word}%'))
        filters.append(DSMetaData.description.ilike(f'%{word}%'))
        filters.append(Author.name.ilike(f'%{word}%'))
        filters.append(FMMetaData.uvl_filename.ilike(f'%{word}%'))
        filters.append(DSMetaData.tags.ilike(f'%{word}%'))

    datasets = DataSet.query \
        .join(DSMetaData) \
        .join(Author) \
        .join(FeatureModel) \
        .join(FMMetaData)

    # Filter by publication_type if it is not 'any'
    if publication_type != 'any':
        datasets = datasets.filter(DSMetaData.publication_type == publication_type)

    datasets = datasets.filter(or_(*filters))

    # Order by created_at
    if order == 'oldest':
        datasets = datasets.order_by(DataSet.created_at.asc())
    else:
        datasets = datasets.order_by(DataSet.created_at.desc())

    datasets = datasets.all()

    dataset_dicts = [dataset.to_dict() for dataset in datasets]

    return jsonify(dataset_dicts)
