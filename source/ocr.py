"""Offline OCR for JD screenshots, using the Windows 11 built-in OCR engine
(Windows.Media.Ocr via winsdk). No network, no external binaries.

image_to_text(path) -> str   (raises OcrError with a friendly message on failure)
"""

import asyncio


class OcrError(Exception):
    pass


async def _recognize(path):
    from winsdk.windows.graphics.imaging import BitmapDecoder
    from winsdk.windows.media.ocr import OcrEngine
    from winsdk.windows.storage import StorageFile, FileAccessMode

    engine = OcrEngine.try_create_from_user_profile_languages()
    if engine is None:
        raise OcrError(
            'No Windows OCR language pack is installed. Add one via Settings '
            '→ Time & language → Language, or paste the JD text instead.')

    file = await StorageFile.get_file_from_path_async(path)
    stream = await file.open_async(FileAccessMode.READ)
    decoder = await BitmapDecoder.create_async(stream)
    bitmap = await decoder.get_software_bitmap_async()
    result = await engine.recognize_async(bitmap)
    lines = [ln.text for ln in result.lines]
    return '\n'.join(lines)


def image_to_text(path):
    try:
        import winsdk  # noqa: F401
    except ImportError:
        raise OcrError(
            "Windows OCR support isn't installed. Run: pip install winsdk "
            "(or paste the JD text instead).")
    try:
        return asyncio.run(_recognize(path)).strip()
    except OcrError:
        raise
    except Exception as e:
        raise OcrError(
            'Could not read text from that image (%s). Try a clearer screenshot '
            'or paste the JD text.' % type(e).__name__)
