from .securityUtils import redis

async def is_rate_limited(
    identifier: str,
    action: str,
    max_attempts: int = 5,
    window_seconds: int = 3600
) -> bool:
    """
    Check if an action is rate limited
    
    Args:
        identifier: Usually IP address or user_id
        action: Type of action being rate limited
        max_attempts: Maximum number of attempts allowed
        window_seconds: Time window in seconds
    """
    key = f"ratelimit:{action}:{identifier}"
    
    async with redis.pipeline() as pipe:
        try:
            # Get current count and increment
            current = await redis.get(key)
            
            if current is None:
                # First attempt
                await pipe.set(key, 1, ex=window_seconds)
                await pipe.execute()
                return False
                
            count = int(current)
            if count >= max_attempts:
                return True
                
            # Increment counter
            await pipe.incr(key)
            await pipe.execute()
            return False
            
        except Exception as e:
            # If Redis fails, default to allowing the request
            return False