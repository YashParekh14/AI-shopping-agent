import json
import logging
import os
import re

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain.tools import tool

import config
import catalog
from reviews_api import get_product_rating

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger("shopping_agent")

llm = ChatOpenAI(model=config.TEXT_MODEL, temperature=config.MODEL_TEMPERATURE)
vision_llm = ChatOpenAI(model=config.VISION_MODEL, temperature=config.MODEL_TEMPERATURE)

_MIME_BY_EXT = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}


def _extract_json(text: str):
    """Extract a JSON object from an LLM response, stripping markdown fences."""
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError(f"Could not parse JSON from model output: {text[:200]!r}")



# Tools


@tool
def search_products(
    query: str,
    max_price: float = None,
    is_organic: bool = None,
    min_rating: float = None,
) -> str:
    """Search products by keyword. Returns products WITH their ratings already included.
    Apply all filters in a single call: max_price, is_organic, min_rating.
    Each result has: id, name, category, price, description, is_organic,
    average_rating, review_count. No separate ratings call needed."""
    logger.info(
        "search_products query=%r max_price=%s is_organic=%s min_rating=%s",
        query, max_price, is_organic, min_rating,
    )
    results = catalog.search_products(
        query=query,
        max_price=max_price,
        is_organic=is_organic,
        min_rating=min_rating,
    )
    logger.info("search_products returned %d results", len(results))
    return json.dumps(results)


@tool
def checkout(product_id: int) -> str:
    """Place an order for the given product ID. Only call this after the user
    has explicitly confirmed they want to buy. Returns order confirmation."""
    logger.info("checkout product_id=%s", product_id)
    result = catalog.create_order(product_id)
    if not result["ok"]:
        return f"Error: {result['error']}."
    return (
        f"Order #{result['order_id']} confirmed! '{result['product_name']}' has been "
        f"successfully ordered for ${result['price']:.2f}. "
        f"Your order will arrive in 3-5 business days. Thank you for shopping with us!"
    )


@tool
def describe_product_image(image_path: str) -> str:
    """Analyze a product image and return its attributes as JSON.
    Use when the user uploads a photo. Returns: product_type, search_query,
    is_organic, description."""
    logger.info("describe_product_image path=%s", image_path)
    if not os.path.isfile(image_path):
        return json.dumps({"error": f"image not found at path: {image_path}"})

    try:
        with open(image_path, "rb") as f:
            import base64
            image_data = base64.b64encode(f.read()).decode()
    except OSError as exc:
        logger.exception("failed to read image")
        return json.dumps({"error": f"could not read image: {exc}"})

    ext = os.path.splitext(image_path)[1].lower().lstrip(".")
    mime = _MIME_BY_EXT.get(ext, "image/jpeg")

    message = HumanMessage(content=[
        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_data}"}},
        {
            "type": "text",
            "text": (
                "Look at this product image and extract its key attributes. "
                "Return ONLY a JSON object with these fields:\n"
                "- product_type: what kind of product it is\n"
                "- search_query: a short keyword to search for it\n"
                "- is_organic: true if the label says organic, false if not, null if unclear\n"
                "- description: one sentence describing the product"
            ),
        },
    ])

    try:
        response = vision_llm.invoke([message])
        attributes = _extract_json(response.content)
    except Exception as exc:
        logger.exception("vision analysis failed")
        return json.dumps({"error": f"could not analyze image: {exc}"})

    return json.dumps(attributes)



# Tools list


TOOLS = [search_products, checkout, describe_product_image]

SYSTEM_PROMPT = """You are a helpful shopping assistant with access to a product catalog.

BROWSING — when the user wants to find products:
1. Call search_products with ALL filters at once: query, max_price, is_organic, min_rating.
   The results already include ratings — no separate ratings call needed.
2. Present the results as a numbered list in this exact format (plain text only):

#<number>. <name> (ID:<id>) — $<price> ★<average_rating> — <organic or non-organic>

Add a blank line between products. Always include (ID:X) for later reference.
3. Ask: 'Would you like to order one? Just say yes or give me the number.'
4. Do NOT call checkout yet.

IMAGE SEARCH — when the user uploads an image:
1. Call describe_product_image to identify the product.
2. Use the returned search_query and is_organic with search_products.
3. Present results as above.

ORDERING — when the user confirms (e.g. 'yes', 'order number 2', 'the first one'):
1. Find the (ID:X) from your previous message for the chosen product.
2. Call checkout with that product_id.
3. Confirm the order in plain text.

Rules:
- Never call checkout without explicit user confirmation.
- Never guess a product_id — use the ID from your previous message.
- If search returns no results, say so clearly and suggest broadening the search."""



# Agent with manual tool-call loop


class Agent:
    def __init__(self, llm, tools, system_prompt):
        self.llm = llm.bind_tools(tools)
        self.tools = {t.name: t for t in tools}
        self.system_prompt = system_prompt

    def invoke(self, input_dict: dict) -> dict:
        messages = [SystemMessage(content=self.system_prompt)]

        for m in input_dict.get("messages", []):
            if isinstance(m, dict):
                if m["role"] == "user":
                    messages.append(HumanMessage(content=m["content"]))
                elif m["role"] == "assistant":
                    messages.append(AIMessage(content=m["content"]))
            else:
                messages.append(m)

        for _ in range(10):
            response = self.llm.invoke(messages)
            messages.append(response)

            if not response.tool_calls:
                break

            for tc in response.tool_calls:
                tool_fn = self.tools.get(tc["name"])
                if tool_fn is None:
                    result = f"Error: unknown tool {tc['name']}"
                else:
                    try:
                        result = tool_fn.invoke(tc["args"])
                        logger.info("tool %s returned: %s", tc["name"], str(result)[:200])
                    except Exception as exc:
                        result = f"Error running {tc['name']}: {exc}"
                        logger.exception("tool %s failed", tc["name"])

                messages.append(ToolMessage(
                    content=str(result),
                    tool_call_id=tc["id"],
                ))

        return {"messages": messages}


agent = Agent(llm=llm, tools=TOOLS, system_prompt=SYSTEM_PROMPT)


if __name__ == "__main__":
    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": "I want organic honey under $20 with 4.5+ rating.",
        }]
    })
    print(result["messages"][-1].content)
