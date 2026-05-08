from accounts.models import Worker


def worker_context(request):
    worker_id = request.session.get('worker_id')
    if worker_id:
        try:
            return {'worker': Worker.objects.get(id=worker_id)}
        except Worker.DoesNotExist:
            pass
    return {'worker': None}
