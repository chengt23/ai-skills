from __future__ import annotations

import io
import re
import tarfile
from tempfile import NamedTemporaryFile


def extract_markdown_from_pdf_bytes(pdf_bytes: bytes) -> str | None:
    if not pdf_bytes:
        return None

    try:
        import pymupdf  # type: ignore
        import pymupdf.layout  # type: ignore

        pymupdf.TOOLS.mupdf_display_errors(False)
        pymupdf.layout.activate()
        import pymupdf4llm  # type: ignore

        with NamedTemporaryFile(suffix=".pdf") as handle:
            handle.write(pdf_bytes)
            handle.flush()
            text = pymupdf4llm.to_markdown(
                handle.name,
                use_ocr=False,
                header=False,
                footer=False,
                ignore_code=True,
            )
            return _normalize_extracted_text(text)
    except Exception:
        pass

    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return _normalize_extracted_text("\n".join(pages))
    except Exception:
        return None


def extract_tex_code_from_tar_bytes(tar_bytes: bytes, paper_id: str) -> str | None:
    try:
        archive = tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:gz")
    except tarfile.ReadError:
        return None

    with archive:
        tex_files = [member for member in archive.getnames() if member.endswith(".tex")]
        if not tex_files:
            return None

        bbl_files = [member for member in archive.getnames() if member.endswith(".bbl")]
        if len(bbl_files) == 1:
            candidate = bbl_files[0].removesuffix(".bbl") + ".tex"
            main_tex = candidate if candidate in tex_files else None
        elif len(tex_files) == 1:
            main_tex = tex_files[0]
        else:
            main_tex = None

        file_contents: dict[str, str] = {}
        for name in tex_files:
            extracted = archive.extractfile(name)
            if extracted is None:
                continue
            content = extracted.read().decode("utf-8", errors="ignore")
            content = re.sub(r"%.*\n", "\n", content)
            content = re.sub(r"\\begin{comment}.*?\\end{comment}", "", content, flags=re.DOTALL)
            content = re.sub(r"\\iffalse.*?\\fi", "", content, flags=re.DOTALL)
            content = re.sub(r"\n+", "\n", content)
            content = re.sub(r"\\\\", "", content)
            content = re.sub(r"[ \t\r\f]{3,}", " ", content)
            file_contents[name] = content
            if main_tex is None and re.search(r"\\begin\{document\}", content) and not any(
                marker in name for marker in ("example", "sample")
            ):
                main_tex = name

        if main_tex is None:
            return None

        main_source = file_contents.get(main_tex)
        if not main_source:
            return None

        include_files = re.findall(r"\\input\{(.+?)\}", main_source) + re.findall(r"\\include\{(.+?)\}", main_source)
        for included in include_files:
            file_name = included if included.endswith(".tex") else f"{included}.tex"
            main_source = main_source.replace(f"\\input{{{included}}}", file_contents.get(file_name, ""))
            main_source = main_source.replace(f"\\include{{{included}}}", file_contents.get(file_name, ""))
        return _normalize_extracted_text(main_source)


def _normalize_extracted_text(text: str | None) -> str | None:
    if not text:
        return None
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return None
    return normalized[:50000]
