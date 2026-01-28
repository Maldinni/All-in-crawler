import time
import tweepy

from config.settings import X_BEARER_TOKEN  

client = tweepy.Client(bearer_token=X_BEARER_TOKEN, wait_on_rate_limit=False)

try:
    resp = client.search_recent_tweets(
        query='piaui lang:pt -is:retweet -is:reply',
        max_results=10,
        tweet_fields=["created_at","author_id"],
    )
    print("ok:", len(resp.data or []))
except tweepy.TooManyRequests as e:
    h = e.response.headers
    print("429 remaining:", h.get("x-rate-limit-remaining"))
    print("reset(epoch):", h.get("x-rate-limit-reset"))
    if h.get("x-rate-limit-reset"):
        wait = int(h["x-rate-limit-reset"]) - int(time.time())
        print("wait(s):", max(wait, 0))
