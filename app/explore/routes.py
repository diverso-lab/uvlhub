import unidecode

from flask import render_template, request, abort, jsonify
from sqlalchemy import or_

from . import explore_bp
from .forms import ExploreForm
from ..dataset.models import DataSet, DSMetaData, Author, FeatureModel, FMMetaData


@explore_bp.route('/explore', methods=['GET'])
def index():
    form = ExploreForm()
    return render_template('explore/index.html', form=form)


@explore_bp.route('/explore', methods=['POST'])
def explore():
    criteria = request.get_json()

    query = criteria.get('query', '')
    sorting = criteria.get('sorting', 'newest')
    publication_type = criteria.get('publication_type')

    # Normalize
    normalized_query = unidecode.unidecode(query).lower()

    # Split the query into words
    words = normalized_query.split()

    # Build the query
    data_query = DataSet.query \
        .join(DSMetaData) \
        .join(Author) \
        .join(FeatureModel) \
        .join(FMMetaData)

    # Filter by each word in the query
    for word in words:
        data_query = data_query.filter(or_(
            DSMetaData.title.ilike(f'%{word}%'),
            DSMetaData.description.ilike(f'%{word}%'),
            Author.name.ilike(f'%{word}%'),
            FMMetaData.uvl_filename.ilike(f'%{word}%'),
        ))

    # Filter by publication type if provided and not 'any'
    if publication_type is not None and publication_type != 'any':
        data_query = data_query.filter(DSMetaData.publication_type == publication_type)

    # Apply sorting
    if sorting == 'newest':
        data_query = data_query.order_by(DataSet.created_at.desc())
    else:  # sorting == 'oldest'
        data_query = data_query.order_by(DataSet.created_at.asc())

    datasets = data_query.all()

    return jsonify([dataset.to_dict() for dataset in datasets])
