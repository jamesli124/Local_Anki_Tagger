from pptx.enum.shapes import MSO_SHAPE_TYPE

from Scripts.util.vision_utils import describe_image

# Filters out logos/icons/bullets on otherwise-blank slides: 1 inch in EMU.
MIN_PPTX_IMAGE_EMU = 914400


def describe_pdf_page_if_image_only(page):
    """Given a fitz Page with no extractable text, return a vision description
    of the rendered page if it contains an embedded image, else None (a truly
    blank or divider page)."""
    if not page.get_images(full=True):
        return None
    try:
        pix = page.get_pixmap(dpi=150)
        return describe_image(pix.tobytes("png"))
    except Exception as e:
        print(f"Vision description failed for page {page.number + 1}: {e}")
        return None


def describe_pptx_slide_images(slide):
    """Return a description of any sufficiently large pictures on a
    text-empty slide, or None if the slide has no qualifying images."""
    descriptions = []
    for shape in slide.shapes:
        if shape.shape_type != MSO_SHAPE_TYPE.PICTURE:
            continue
        if shape.width < MIN_PPTX_IMAGE_EMU or shape.height < MIN_PPTX_IMAGE_EMU:
            continue
        try:
            image = shape.image
            descriptions.append(describe_image(image.blob, image.content_type))
        except Exception as e:
            print(f"Vision description failed for a slide image: {e}")
    return "\n".join(descriptions) if descriptions else None


def get_pptx_slide_notes(slide):
    if slide.has_notes_slide:
        notes = slide.notes_slide.notes_text_frame.text
        if notes and notes.strip():
            return notes.strip()
    return None
