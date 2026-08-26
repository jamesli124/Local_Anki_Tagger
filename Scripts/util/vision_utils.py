import base64

from Scripts.util import config
from Scripts.util.llm_client import client

VISION_SYSTEM_PROMPT = (
    "You are a medical educator describing an image from a lecture slide or page so it can be "
    "used as source material for writing learning objectives. First identify what kind of image "
    "it is (e.g. gross or cadaveric anatomy dissection, histology or pathology slide, radiograph, "
    "CT, MRI, ultrasound, diagram, chart, or clinical photo), then describe the key structures, "
    "labels, and any pathological or abnormal findings that are visible. Be specific and factual; "
    "do not speculate beyond what is visible. Write plain descriptive prose, not a caption."
)


def describe_image(image_bytes, mime_type="image/png"):
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{mime_type};base64,{b64}"

    completion = client.chat.completions.create(
        model=config.CHAT_MODEL,
        messages=[
            {"role": "system", "content": VISION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image."},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ],
        temperature=0.2,
    )

    return completion.choices[0].message.content.strip()
