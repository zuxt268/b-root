
def get_redis():
    if "redis" not in g:
        g.redis = redis.Redis(
            host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT")
        )
    return g.redis