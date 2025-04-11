import asyncio
import os
import sys
from typing import List, Optional, Union
from langchain_community.document_loaders import (
    PyMuPDFLoader,
    TextLoader,
    UnstructuredCSVLoader,
    UnstructuredExcelLoader,
    UnstructuredMarkdownLoader,
    UnstructuredPowerPointLoader,
    UnstructuredWordDocumentLoader
)
from langchain_community.document_loaders import BSHTMLLoader
from langchain_core.documents import Document

try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import (
        VlmModelType,
        VlmPipelineOptions,
        granite_vision_vlm_conversion_options,
        granite_vision_vlm_ollama_conversion_options,
        smoldocling_vlm_conversion_options,
        smoldocling_vlm_mlx_conversion_options,
    )
    from docling.pipeline.vlm_pipeline import VlmPipeline
    HAVE_DOCLING = True
except ImportError:
    HAVE_DOCLING = False


class DoclingLoader:
    """Loader for an individual document that matches langchain API"""

    def __init__(self, file_path: str, vlm: Optional[str] = None):
        if not HAVE_DOCLING:
            raise ImportError("Please install docling to use this function.")
        self.file_path = file_path
        vlm_options = None
        if vlm == VlmModelType.GRANITE_VISION:
            vlm_options = granite_vision_vlm_conversion_options
        elif vlm == VlmModelType.GRANITE_VISION_OLLAMA:
            vlm_options = granite_vision_vlm_ollama_conversion_options
        elif vlm == VlmModelType.SMOLDOCLING:
            vlm_options = smoldocling_vlm_conversion_options
            if sys.platform == "darwin":
                try:
                    import mlx_vlm

                    vlm_options = smoldocling_vlm_mlx_conversion_options
                except ImportError:
                    print("mlx-vlm not installed, falling back to torch")
        elif vlm is not None:
            raise ValueError(f"Unknown docling vlm option: {vlm}")

        format_options = None
        if vlm_options is not None:
            pipeline_options = VlmPipelineOptions(enable_remote_services=True)
            pipeline_options.vlm_options = vlm_options
            pdf_format_option = PdfFormatOption(
                pipeline_cls=VlmPipeline, pipeline_options=pipeline_options
            )
            format_options = {
                InputFormat.PDF: pdf_format_option,
                InputFormat.IMAGE: pdf_format_option,
            }

        self.converter = DocumentConverter(format_options=format_options)

    def load(self) -> list[Document]:
        assert HAVE_DOCLING
        res = self.converter.convert(self.file_path)
        doc = Document(
            page_content=res.document.export_to_markdown(),
            metadata={"source": self.file_path}
        )
        return [doc]


class DocumentLoader:

    def __init__(
        self,
        path: Union[str, List[str]],
        use_docling: bool = False,
        docling_vlm: Optional[str] = None,
    ):
        self.path = path
        self.use_docling = use_docling
        self.docling_vlm = docling_vlm

    async def load(self) -> list:
        tasks = []
        if isinstance(self.path, list):
            for file_path in self.path:
                if os.path.isfile(file_path):  # Ensure it's a valid file
                    filename = os.path.basename(file_path)
                    file_name, file_extension_with_dot = os.path.splitext(filename)
                    file_extension = file_extension_with_dot.strip(".").lower()
                    tasks.append(self._load_document(file_path, file_extension))

        elif isinstance(self.path, (str, bytes, os.PathLike)):
            for root, dirs, files in os.walk(self.path):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_name, file_extension_with_dot = os.path.splitext(file)
                    file_extension = file_extension_with_dot.strip(".").lower()
                    tasks.append(self._load_document(file_path, file_extension))

        else:
            raise ValueError("Invalid type for path. Expected str, bytes, os.PathLike, or list thereof.")

        docs = []
        for pages in await asyncio.gather(*tasks):
            for page in pages:
                if page.page_content:
                    docs.append({
                        "raw_content": page.page_content,
                        "url": os.path.basename(page.metadata['source'])
                    })

        if not docs:
            raise ValueError("🤷 Failed to load any documents!")

        return docs

    async def _load_document(self, file_path: str, file_extension: str) -> list:
        ret_data = []
        try:
            if self.use_docling and HAVE_DOCLING:
                docling_loader = DoclingLoader(file_path, self.docling_vlm)
                loader_dict = {
                    "pdf": docling_loader,
                    "txt": TextLoader(file_path),
                    "doc": docling_loader,
                    "docx": docling_loader,
                    "pptx": docling_loader,
                    "csv": docling_loader,
                    "xls": docling_loader,
                    "xlsx": docling_loader,
                    "md": UnstructuredMarkdownLoader(file_path),
                    "html": BSHTMLLoader(file_path),
                    "htm": BSHTMLLoader(file_path),
                    "png": docling_loader,
                    "jpg": docling_loader,
                    "jpeg": docling_loader,
                }

            else:
                loader_dict = {
                    "pdf": PyMuPDFLoader(file_path),
                    "txt": TextLoader(file_path),
                    "doc": UnstructuredWordDocumentLoader(file_path),
                    "docx": UnstructuredWordDocumentLoader(file_path),
                    "pptx": UnstructuredPowerPointLoader(file_path),
                    "csv": UnstructuredCSVLoader(file_path, mode="elements"),
                    "xls": UnstructuredExcelLoader(file_path, mode="elements"),
                    "xlsx": UnstructuredExcelLoader(file_path, mode="elements"),
                    "md": UnstructuredMarkdownLoader(file_path),
                    "html": BSHTMLLoader(file_path),
                    "htm": BSHTMLLoader(file_path)
                }

            loader = loader_dict.get(file_extension, None)
            if loader:
                try:
                    ret_data = loader.load()
                except Exception as e:
                    print(f"Failed to load HTML document : {file_path}")
                    print(e)

        except Exception as e:
            print(f"Failed to load document : {file_path}")
            print(e)

        return ret_data
