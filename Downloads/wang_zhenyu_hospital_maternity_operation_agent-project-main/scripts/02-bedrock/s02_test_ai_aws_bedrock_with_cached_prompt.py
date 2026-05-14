# -*- coding: utf-8 -*-

"""
Prompt Caching with Amazon Bedrock

Demonstrates how prompt caching reduces costs for static content.

COST SAVINGS: Up to 75% reduction on cached input tokens.
- First call: Tokens WRITTEN to cache (normal price)
- Subsequent calls: Tokens READ from cache (~25% of normal price!)

IMPORTANT: Minimum token requirement!
- Nova Micro/Lite/Pro: 1,024 tokens minimum
- Claude models: 1,024 - 4,096 tokens minimum (varies by model)
- If below minimum, caching silently disabled (no error, just no cache)

HOW IT WORKS:
    [Static content 1000+ tokens] + [cachePoint] + [Question]
                                          ↑
                            Cache boundary marker
"""

import boto3
from dataclasses import dataclass


@dataclass
class ChatResponse:
    """
    Response from a cached chat API call.

    Attributes:
        text: The AI's response text
        input_tokens: Tokens in the dynamic part (question)
        output_tokens: Tokens in the AI response
        total_tokens: Total tokens processed
        cache_write_tokens: Tokens written TO cache (first call only)
        cache_read_tokens: Tokens read FROM cache (subsequent calls)

    How to interpret cache metrics:
        - cache_write_tokens > 0: Static content was written to cache (pay normal price)
        - cache_read_tokens > 0: Static content was read from cache (pay ~25% price!)
        - Both are 0: Caching not triggered (content below minimum token threshold)
    """

    text: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cache_write_tokens: int
    cache_read_tokens: int

    @property
    def cache_hit(self) -> bool:
        """True if we read from cache (saving money!)"""
        return self.cache_read_tokens > 0

    @property
    def cache_miss(self) -> bool:
        """True if we wrote to cache (first call or cache expired)"""
        return self.cache_write_tokens > 0


def create_bedrock_client():
    """Create Bedrock runtime client."""
    session = boto3.Session()
    return session.client(service_name="bedrock-runtime", region_name="us-east-1")


def send_message_with_cache(
    client,
    model_id: str,
    static_context: str,
    question: str,
) -> ChatResponse:
    """
    Send a message with prompt caching enabled.

    Args:
        client: Bedrock runtime client
        model_id: Model ID to use
        static_context: Text that stays the same (will be cached, needs 1024+ tokens)
        question: Dynamic question (changes each call)

    Returns:
        ChatResponse dataclass with text and token metrics
    """
    # ==========================================================================
    # BUILD MESSAGE WITH CACHE CHECKPOINT
    # ==========================================================================
    # The message content is a LIST of content blocks.
    # The cachePoint block marks where the cache boundary is.
    # Everything BEFORE cachePoint will be cached.
    # Everything AFTER cachePoint is dynamic (not cached).
    messages = [
        {
            "role": "user",
            "content": [
                # ---------------------------------------------------------------
                # STATIC CONTENT (will be cached)
                # This is the long text that stays the same across API calls.
                # It must be at least 1024 tokens for caching to activate.
                # ---------------------------------------------------------------
                {"text": static_context},

                # ---------------------------------------------------------------
                # CACHE CHECKPOINT (the magic!)
                # This tells Bedrock: "Cache everything before this point"
                # Format: {"cachePoint": {"type": "default"}}
                # Optional: Add "ttl": "5m" or "1h" for cache duration
                # ---------------------------------------------------------------
                {"cachePoint": {"type": "default"}},

                # ---------------------------------------------------------------
                # DYNAMIC CONTENT (not cached)
                # This is the question that changes each time.
                # It comes AFTER the cachePoint so it's not cached.
                # ---------------------------------------------------------------
                {"text": question},
            ],
        }
    ]

    # ==========================================================================
    # CALL THE API
    # ==========================================================================
    response = client.converse(
        modelId=model_id,
        messages=messages,
        system=[{"text": "You are a helpful assistant. Keep responses brief."}],
        inferenceConfig={"maxTokens": 100, "temperature": 0.7},
    )

    # ==========================================================================
    # EXTRACT USAGE METRICS
    # ==========================================================================
    # The usage dict contains these key fields:
    #
    # - inputTokens: Tokens in the DYNAMIC part only (question)
    # - outputTokens: Tokens in the AI response
    # - totalTokens: All tokens processed (static + dynamic + output)
    #
    # - cacheWriteInputTokens: How many tokens were WRITTEN to cache
    #   > 0 means this is the FIRST call (or cache expired)
    #   = 0 means cache already exists
    #
    # - cacheReadInputTokens: How many tokens were READ from cache
    #   > 0 means we HIT the cache (saving 75% on these tokens!)
    #   = 0 means cache miss or first call
    #
    usage = response.get("usage", {})

    return ChatResponse(
        text=response["output"]["message"]["content"][0]["text"],
        input_tokens=usage.get("inputTokens", 0),
        output_tokens=usage.get("outputTokens", 0),
        total_tokens=usage.get("totalTokens", 0),
        cache_write_tokens=usage.get("cacheWriteInputTokens", 0),
        cache_read_tokens=usage.get("cacheReadInputTokens", 0),
    )


def print_turn(turn: int, question: str, response: ChatResponse):
    """Print a conversation turn with token metrics."""
    print(f"\n{'='*60}")
    print(f"TURN {turn}")
    print(f"{'='*60}")
    print(f"Q: {question}")
    print(f"A: {response.text}")

    print(f"\nTokens: input={response.input_tokens}, output={response.output_tokens}, total={response.total_tokens}")
    print(f"Cache:  write={response.cache_write_tokens}, read={response.cache_read_tokens}", end="")

    if response.cache_miss:
        print("  <-- Writing to cache")
    elif response.cache_hit:
        print("  <-- Cache hit (75% cheaper!)")
    else:
        print()


# =============================================================================
# Demo
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("PROMPT CACHING DEMO")
    print("=" * 60)
    print("""
IMPORTANT: Prompt caching requires minimum 1024 tokens!
This demo uses a long profile (~900 tokens) to trigger caching.

Watch the Cache line:
- Turn 1: write > 0 (tokens written to cache)
- Turn 2-3: read > 0 (tokens read from cache = 75% savings!)
""")

    client = create_bedrock_client()
    model_id = "us.amazon.nova-micro-v1:0"

    # Static context: Personal profile (~900 tokens to meet minimum)
    profile = """
=== PERSONAL PROFILE ===

BASIC INFORMATION:
My name is Emily Thompson. I am a 28-year-old marketing manager currently
living and working in Denver, Colorado. I grew up in a small town in Vermont
and moved to Colorado after graduating from Boston University with a degree
in Communications and a minor in Environmental Studies.

CAREER BACKGROUND:
I work at a sustainable outdoor apparel company where I lead our digital
marketing efforts. My job involves creating content, managing social media
campaigns, and building partnerships with environmental nonprofits. Before
this role, I worked at a traditional advertising agency in Boston for three
years. I love that my current job combines my passion for the outdoors with
meaningful work that promotes sustainability.

PERSONALITY AND VALUES:
I consider myself an extrovert who thrives on connecting with people and
building community. I value authenticity, environmental responsibility, and
living life with intention. I believe small daily choices can make a big
difference for our planet. I try to live by the principle of leaving places
better than I found them, whether that means picking up trash on a trail or
mentoring junior colleagues at work.

FAVORITES AND PREFERENCES:
Color: My favorite color is forest green. It reminds me of hiking through
Vermont woods as a child with my grandfather. The color represents growth,
nature, and the peace I find outdoors.

Fruit: I absolutely love blueberries. Growing up in Vermont, we would pick
wild blueberries every August. My grandmother made the best blueberry pie,
and the taste always brings back warm summer memories.

Sport: Trail running is my favorite activity. I run on mountain trails near
Denver almost every weekend. The combination of physical challenge and
stunning scenery keeps me grounded and energized.

Music: I am a huge fan of folk and indie music. Artists like The Lumineers,
Bon Iver, and Phoebe Bridgers are always on my playlists. I also love
discovering local musicians at small venues around Denver.

Movie: Wild with Reese Witherspoon is my all-time favorite movie. The story
of self-discovery through hiking the Pacific Crest Trail resonates deeply
with me. I have watched it many times and it always inspires me.

Food: I enjoy farm-to-table cuisine and love cooking with locally sourced
ingredients. I visit the farmers market every Saturday morning and plan my
weekly meals around what is fresh and in season.

HOBBIES AND INTERESTS:
Hiking: Living in Colorado gives me access to incredible hiking trails. I
try to summit at least one fourteener each summer. Some of my favorite
trails are in Rocky Mountain National Park and the Maroon Bells area.

Photography: I love landscape and nature photography. I always carry my
camera on hikes and have sold some prints at local art fairs. Capturing
the beauty of Colorado keeps me present in the moment.

Volunteering: I regularly volunteer with trail maintenance crews and lead
hiking groups for a local outdoor club focused on getting more women into
backcountry adventures.

Reading: I enjoy memoirs, nature writing, and books about sustainability.
Some authors I admire include Cheryl Strayed, Robin Wall Kimmerer, and
Michael Pollan.

GOALS AND ASPIRATIONS:
Short-term: Complete my first ultramarathon this fall. I have been training
for months and am excited for the challenge. I also want to earn my
wilderness first responder certification.

Long-term: My dream is to start a nonprofit that provides outdoor experiences
for underserved youth. I believe everyone deserves access to nature and the
mental health benefits it provides. I am currently saving money and building
connections to make this dream a reality.

COMMUNICATION STYLE:
I am warm and enthusiastic in my communication. I love asking questions and
really listening to peoples stories. I believe in honest, direct feedback
delivered with kindness. I try to be encouraging and supportive while also
being genuine about challenges.

WORK STYLE:
I am most creative in the mornings and like to tackle big projects then. I
thrive in collaborative environments and enjoy brainstorming sessions. I
value work-life balance and protect my weekends for outdoor adventures and
time with friends and family.

=== END OF PROFILE ===
"""

    # Turn 1: First question (cache WRITES)
    q1 = "Based on my profile, what birthday gift would you recommend?"
    r1 = send_message_with_cache(client, model_id, profile, q1)
    print_turn(1, q1, r1)

    # Turn 2: Second question (cache READS - 75% savings!)
    q2 = "What weekend activity would suit me?"
    r2 = send_message_with_cache(client, model_id, profile, q2)
    print_turn(2, q2, r2)

    # Turn 3: Third question (cache READS again)
    q3 = "What music playlist matches my personality?"
    r3 = send_message_with_cache(client, model_id, profile, q3)
    print_turn(3, q3, r3)

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    print(f"Turn 1: wrote {r1.cache_write_tokens} tokens to cache")
    print(f"Turn 2: read {r2.cache_read_tokens} tokens from cache")
    print(f"Turn 3: read {r3.cache_read_tokens} tokens from cache")

    total_read = r2.cache_read_tokens + r3.cache_read_tokens
    if total_read > 0:
        print(f"\nCost savings: {total_read} cached tokens x 75% = ~{total_read * 0.75:.0f} tokens worth saved!")
