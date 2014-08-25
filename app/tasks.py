from app.extensions import celery

@celery.task
def delete_index(model_index, model_id):
    with model_index.writer() as writer:
        writer.delete_by_term("model_id", unicode(model_id))

@celery.task
def update_index(model_index, attrs):
   with model_index.writer() as writer:
        writer.update_document(**attrs)
